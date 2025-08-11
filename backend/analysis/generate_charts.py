import json
import os
from pathlib import Path
from collections import Counter

import matplotlib.pyplot as plt


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_intent_report(nlu_results_dir: Path) -> dict:
    # Try common filenames produced by Rasa
    candidates = [
        nlu_results_dir / "intent_report.json",
        nlu_results_dir / "report.json",
    ]
    for file in candidates:
        if file.exists():
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


def plot_intent_metrics(report: dict, out_dir: Path) -> None:
    if not report:
        print("No intent report found. Skipping intent metrics plots.")
        return

    # Rasa intent_report.json structure: keys are intents and 'accuracy'/'macro avg'/etc.
    intents = [k for k in report.keys() if k not in {"accuracy", "weighted avg", "macro avg", "micro avg"}]
    intents.sort()

    precisions = [report[i].get("precision", 0.0) for i in intents]
    recalls = [report[i].get("recall", 0.0) for i in intents]
    f1s = [report[i].get("f1-score", 0.0) for i in intents]
    supports = [report[i].get("support", 0) for i in intents]

    plt.style.use("ggplot")
    cmap = plt.get_cmap("tab20")

    def barplot(values, title, filename, ylabel="Score"):
        plt.figure(figsize=(max(8, len(intents) * 0.5), 5))
        colors = [cmap(i % 20) for i in range(len(intents))]
        plt.bar(intents, values, color=colors)
        plt.xticks(rotation=60, ha="right")
        plt.ylim(0, 1.05 if ylabel == "Score" else max(values + [1]))
        plt.ylabel(ylabel)
        plt.title(title)
        plt.tight_layout()
        plt.savefig(out_dir / filename, dpi=200)
        plt.close()

    barplot(precisions, "Intent Precision by Class", "intent_precision.png")
    barplot(recalls, "Intent Recall by Class", "intent_recall.png")
    barplot(f1s, "Intent F1-score by Class", "intent_f1.png")

    # Support plot
    plt.figure(figsize=(max(8, len(intents) * 0.5), 5))
    colors = [cmap(i % 20) for i in range(len(intents))]
    plt.bar(intents, supports, color=colors)
    plt.xticks(rotation=60, ha="right")
    plt.ylabel("Examples (support)")
    plt.title("Support per Intent (Test Set)")
    plt.tight_layout()
    plt.savefig(out_dir / "intent_support.png", dpi=200)
    plt.close()

    # Overall accuracy if available
    acc = report.get("accuracy")
    if isinstance(acc, (int, float)):
        plt.figure(figsize=(4, 4))
        plt.bar(["Accuracy"], [acc], color=cmap(0))
        plt.ylim(0, 1.05)
        plt.ylabel("Score")
        plt.title("NLU Overall Accuracy")
        plt.tight_layout()
        plt.savefig(out_dir / "nlu_overall_accuracy.png", dpi=200)
        plt.close()


def plot_training_examples_per_intent(nlu_path: Path, out_dir: Path) -> None:
    try:
        # Use Rasa's loader to parse NLU YML
        from rasa.shared.nlu.training_data.loading import load_data
    except Exception as e:
        print(f"Could not import Rasa loader to parse NLU file: {e}")
        return

    try:
        td = load_data(str(nlu_path))
    except Exception as e:
        print(f"Failed to load NLU data from {nlu_path}: {e}")
        return

    intents = [ex.get("intent") for ex in td.intent_examples if ex.get("intent")]
    counts = Counter(intents)
    if not counts:
        print("No intents found in training data.")
        return

    labels, values = zip(*sorted(counts.items(), key=lambda kv: kv[0]))

    plt.style.use("ggplot")
    cmap = plt.get_cmap("tab20")
    colors = [cmap(i % 20) for i in range(len(labels))]

    plt.figure(figsize=(max(8, len(labels) * 0.5), 5))
    plt.bar(labels, values, color=colors)
    plt.xticks(rotation=60, ha="right")
    plt.ylabel("Examples")
    plt.title("Training Examples per Intent")
    plt.tight_layout()
    plt.savefig(out_dir / "training_examples_per_intent.png", dpi=200)
    plt.close()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    rasa_dir = repo_root / "backend" / "rasa_core"
    out_dir = repo_root / "docs" / "charts"
    ensure_dir(out_dir)

    # 1) Plot metrics from Rasa NLU test results (if present)
    nlu_results_dir = rasa_dir / "results" / "nlu"
    report = load_intent_report(nlu_results_dir)
    plot_intent_metrics(report, out_dir)

    # 2) Plot dataset distribution from training data
    nlu_path = rasa_dir / "data" / "nlu.yml"
    if nlu_path.exists():
        plot_training_examples_per_intent(nlu_path, out_dir)
    else:
        print(f"NLU file not found at {nlu_path}")

    # 3) Plot intent frequencies appearing in stories (rough count via YAML lines)
    stories_path = rasa_dir / "data" / "stories.yml"
    if stories_path.exists():
        try:
            intents_counter: Counter[str] = Counter()
            with open(stories_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_stripped = line.strip()
                    if line_stripped.startswith("- intent:"):
                        # e.g., "- intent: greet"
                        parts = line_stripped.split(":", 1)
                        if len(parts) == 2:
                            intent_name = parts[1].strip()
                            intents_counter[intent_name] += 1

            if intents_counter:
                labels, values = zip(*sorted(intents_counter.items(), key=lambda kv: kv[0]))
                plt.style.use("ggplot")
                cmap = plt.get_cmap("tab20")
                colors = [cmap(i % 20) for i in range(len(labels))]

                plt.figure(figsize=(max(8, len(labels) * 0.5), 5))
                plt.bar(labels, values, color=colors)
                plt.xticks(rotation=60, ha="right")
                plt.ylabel("Occurrences in Stories")
                plt.title("Intent Frequency in Stories")
                plt.tight_layout()
                plt.savefig(out_dir / "stories_intent_frequency.png", dpi=200)
                plt.close()
        except Exception as e:
            print(f"Failed to analyze stories intents: {e}")

    print(f"Charts generated in: {out_dir}")


if __name__ == "__main__":
    main()


