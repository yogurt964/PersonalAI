import importlib
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


class Benchmark:
    """軽量性確認用の小さなベンチマーク実行クラスです。"""

    def __init__(self):
        self.results = []
        self.personal_ai_class = None
        self.personal_ai = None

    def run(self):
        started_at = time.perf_counter()

        print("PersonalAI Lightweight Benchmark")
        print("================================")
        print()

        self.measure("import_time_personal_ai", self.import_personal_ai)
        self.measure("personal_ai_init_time", self.initialize_personal_ai)
        self.measure("capability_analyze_time", self.benchmark_capability_analyze)
        self.measure("preference_extract_time", self.benchmark_preference_extract)
        self.measure("preference_confirmation_time", self.benchmark_preference_confirmation)
        self.measure("memory_context_build_time", self.benchmark_memory_context_build)
        self.measure("forgetting_dry_run_time", self.benchmark_forgetting_dry_run)

        total_time = time.perf_counter() - started_at
        print()
        print(f"[OK] total_benchmark_time: {format_seconds(total_time)} sec")
        print(f"Total: {format_seconds(total_time)} sec")

    def measure(self, name, function):
        started_at = time.perf_counter()

        try:
            function()
        except SkipBenchmark as skip:
            elapsed = time.perf_counter() - started_at
            print(f"[SKIP] {name}: {skip} ({format_seconds(elapsed)} sec)")
            self.results.append((name, "SKIP", elapsed))
            return
        except Exception as error:
            elapsed = time.perf_counter() - started_at
            print(f"[NG] {name}: {error} ({format_seconds(elapsed)} sec)")
            self.results.append((name, "NG", elapsed))
            return

        elapsed = time.perf_counter() - started_at
        print(f"[OK] {name}: {format_seconds(elapsed)} sec")
        self.results.append((name, "OK", elapsed))

    def import_personal_ai(self):
        module = importlib.import_module("core.personal_ai")
        self.personal_ai_class = module.PersonalAI

    def initialize_personal_ai(self):
        if self.personal_ai_class is None:
            raise SkipBenchmark("PersonalAI importが成功していないためskip")

        self.personal_ai = self.personal_ai_class()

    def benchmark_capability_analyze(self):
        from core.capability_manager import CapabilityManager
        from core.input_analyzer import InputAnalyzer

        analyzer = InputAnalyzer()
        manager = CapabilityManager()
        samples = [
            "こんにちは",
            "私はラーメンが好きです。覚えて",
            "https://example.com を要約して",
            "このPDFを読んで",
            "VS Codeを開いて",
        ]

        for sample in samples:
            input_analysis = analyzer.analyze(sample)
            manager.analyze(sample, input_analysis)

    def benchmark_preference_extract(self):
        from ai.preference_memory import extract_preference_memories

        samples = [
            "ラーメンが好きです。覚えて",
            "寿司は嫌いです。覚えて",
            "カレーは好きじゃないです。覚えて",
        ]

        for sample in samples:
            extract_preference_memories(sample)

    def benchmark_preference_confirmation(self):
        from ai.preference_confirmation import (
            analyze_preference_confirmation,
            resolve_preference_confirmation_answer,
        )

        analyze_preference_confirmation("一番好きな食べ物は焼き肉です。覚えて")
        analyze_preference_confirmation("前はカレーが好きだったけど、今は焼き肉が好きです。覚えて")
        resolve_preference_confirmation_answer(
            "一番好きとして記憶して",
            {
                "type": "preference_confirmation",
                "reason": "primary_preference_update",
                "target": "焼き肉",
                "domain": "food",
            },
        )

    def benchmark_memory_context_build(self):
        from ai.memory_context import build_memory_context
        from database.memory_manager import get_memories

        memories = get_memories(limit=20, active_only=True)
        build_memory_context(memories)

    def benchmark_forgetting_dry_run(self):
        from ai.memory_forgetting import get_forgetting_candidates

        get_forgetting_candidates(limit=100, max_candidates=20, min_score=50)


class SkipBenchmark(Exception):
    """測定を安全にskipしたい場合に使います。"""


def format_seconds(value):
    return f"{value:.3f}"


def main():
    Benchmark().run()


if __name__ == "__main__":
    main()
