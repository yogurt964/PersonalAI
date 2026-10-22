"""Free, synthetic two-process persistence demo. Never opens the real user DB."""
import argparse
import json
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.conversation_api_memory import MemoryApiSession
from core.conversation_memory_workspace import MemoryWorkspace


class DemoClient:
    """Deterministic fixture responses, not an LLM quality evaluation."""
    def __init__(self, output):
        self.output, self.requests, self.responses = output, [], self

    def create(self, **request):
        self.requests.append(request)
        return SimpleNamespace(status='completed', output_text=self.output,
                               usage=SimpleNamespace(input_tokens=0, output_tokens=0))

    def close(self):
        pass


class DemoStore:
    def __init__(self, path):
        self.path = path

    def history(self):
        with closing(sqlite3.connect(self.path)) as db:
            return [{'role': role, 'content': content} for role, content in
                    db.execute('SELECT role,content FROM conversations ORDER BY id')]

    def memories(self):
        return []

    def save_turn(self, user, answer):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executemany('INSERT INTO conversations(role,content,created_at) VALUES (?,?,?)',
                           [(role, content, '2026-10-22T00:00:00+00:00')
                            for role, content in [('user', user), ('assistant', answer)]])


def phase(root, name):
    source, target = root / 'fictional.db', root / 'short.sqlite3'
    if name == 'save':
        if source.exists() or target.exists():
            raise ValueError('demo requires unused temporary paths')
        with closing(sqlite3.connect(source)) as db, db:
            db.execute('CREATE TABLE conversations(id INTEGER PRIMARY KEY,role TEXT,content TEXT,created_at TEXT)')
        store = DemoStore(source)
        store.save_turn('週末の予定は未決定。今日は質問なし。', '了解。')
        candidates = [{'key': key, 'kind': kind, 'content': text, 'tags': [],
                       'evidence': [{'source_id': 1, 'quote': text}]} for key, kind, text in
                      [('weekend', 'open_question', '週末の予定は未決定。'),
                       ('today', 'temporary_preference', '今日は質問なし。')]]
        client = DemoClient(json.dumps({'candidates': candidates}, ensure_ascii=False))
        workspace = MemoryWorkspace(target, source)
        ai = MemoryApiSession('0.25', allow_saved_context=True, store=store,
                              workspace=workspace, client_factory=lambda: client)
        ai.extract_candidates()
        assert not workspace.state.notes
        ai.accept_candidates([1, 2])
        ai.close()
        print('プロセス1: 候補2件を明示採用し、短期記憶と出典の統計を保存。', flush=True)
    else:
        workspace = MemoryWorkspace(target, source)
        assert [n.key for n in workspace.state.notes] == ['weekend']
        assert workspace.ledgers['weekend'].summary(now=workspace.clock(), window_days=30)['total_counts']['mention'] == 1
        print('プロセス2: 未決定の予定と利用統計を復元。一時希望は解除。', flush=True)
        client = DemoClient('架空APIの固定返答です。')
        ai = MemoryApiSession('0.25', allow_saved_context=True, store=DemoStore(source),
                              workspace=workspace, client_factory=lambda: client)
        ai.reply('前の予定の話を続けよう。')
        instructions = client.requests[0]['instructions']
        assert '週末の予定は未決定。' in instructions
        assert '今日は質問なし。' not in instructions
        ai.close()
        restored = MemoryWorkspace(target, source)
        counts = restored.ledgers['weekend'].summary(now=restored.clock(), window_days=30)['total_counts']
        assert counts['context_selected'] == 1 and counts['used_as_evidence'] == 0
        print('次の会話リクエストに復元した要点が入り、文脈選択1回を保存。根拠利用とは数えない。', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('save', 'resume'))
    parser.add_argument('--root', type=Path)
    args = parser.parse_args()
    if args.phase:
        if args.root is None:
            parser.error('--root required for internal phase')
        phase(args.root, args.phase)
        return
    print('架空データ・固定応答のみ。実API・実DB・APIキーは使いません。', flush=True)
    with tempfile.TemporaryDirectory(prefix='personalai-memory-demo-') as root:
        for name in ('save', 'resume'):
            subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()),
                            '--phase', name, '--root', root], check=True)
    print('保存 → プロセス終了 → 別プロセスで復元 → 次の会話で参照、まで確認完了。', flush=True)


if __name__ == '__main__':
    main()
