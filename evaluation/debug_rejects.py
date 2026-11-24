"""אבחון: מדפיס בכל עצירה של הגרף מה הוא מבקש, במקרה של שלוש דחיות."""
from langgraph.types import Command

from evaluation.create_dataset import reject
from src.graph import ITEMS, build_graph, initial_state


def main():
    graph = build_graph()
    config = {"configurable": {"thread_id": "debug"}}
    sequence = [3] * len(ITEMS) + [reject("לא טוב")] * 3

    graph.invoke(initial_state(), config)
    step = 0
    while graph.get_state(config).next:
        payload = graph.get_state(config).tasks[0].interrupts[0].value
        kind = "שאלה" if "question" in payload and "scale" in payload else "החלטת בודק"
        print(f"עצירה {step}: {kind}")
        if step >= len(sequence):
            print("הגרף עדיין מבקש קלט, והרשימה נגמרה.")
            print("payload:", str(payload)[:200])
            break
        graph.invoke(Command(resume=sequence[step]), config)
        step += 1

    values = graph.get_state(config).values
    print("סיום אחרי", step, "צעדים")
    print("revision_count:", values["revision_count"], "final_report:", values["final_report"])


if __name__ == "__main__":
    main()
