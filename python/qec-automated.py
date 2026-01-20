import pyautogui
import random


# The probability to select each option (order is [A, B, C, D])
# Select pre-defined preset, or make a custom one
WEIGHTS: list[float] = [0.25, 0.25, 0.25, 0.25]  # Que Será, Será
# WEIGHTS: list[float] = [1.00, 0.00, 0.00, 0.00]  # Ichigo Ichie
# WEIGHTS: list[float] = [0.35, 0.25, 0.25, 0.15]  # C’est la vie
# WEIGHTS: list[float] = [0.15, 0.25, 0.25, 0.35]  # Il faut imaginer Sisyphe heureux
# WEIGHTS: list[float] = [0.00, 0.00, 0.00, 1.00]  # Weltschmerz
# WEIGHTS: list[float] = [0.00, 0.00, 0.00, 0.00]  # Custom


NUM_MCQS: list[int] = [12, 16, 15]  # 12, 16 and 15 MCQ's respectively per category

# One comment will be randomly selected from this list
COMMENTS_INSTRUCTOR: list[str] = [
    "Beautiful",
]
COMMENTS_COURSE: list[str] = [
    "Beautiful",
]
COMMENTS_ONLINE: list[str] = [
    "Beautiful",
]


def eval_form(category: int, num_subjects: int) -> None:
    mcqs: int = NUM_MCQS[category - 1]

    for _ in range(num_subjects):
        pyautogui.press(["space", "down", "enter"])
        pyautogui.press("tab", presses=6)

        if category == 2:  # "Teacher Evaluation Form" needs one more tab
            pyautogui.press("tab")

        for _ in range(mcqs):
            pyautogui.press("right", presses=random.choices([1, 2, 3, 4], WEIGHTS)[0])
            pyautogui.press("tab")

        match category:
            case 1:  # No comments in "Student Course Evaluation Questionnaire"
                pass
            case 2:
                pyautogui.write(random.choice(COMMENTS_INSTRUCTOR))
                pyautogui.press("tab")
                pyautogui.write(random.choice(COMMENTS_COURSE))
                pyautogui.press("tab")
            case 3:
                pyautogui.write(random.choice(COMMENTS_ONLINE))
                pyautogui.press("tab")

        pyautogui.press("enter")  # submit proforma

        pyautogui.sleep(1)  # wait for form to be submitted
        pyautogui.press("enter")  # confirm OK

        pyautogui.sleep(1)
        pyautogui.press("tab")  # get back in starting position


def main() -> None:
    category: str = input(
        """Which Proforma do you want to fill first? 
1. Student Course Evaluation Questionnaire
2. Teacher Evaluation Form
3. Online Learning Feedback Proforma
>>> """
    ).strip()
    assert category in ["1", "2", "3"], "Please, select 1, 2 or 3"

    subjects: int = int(input("How many subjects/instrutors? "))

    print("Open the desired form and focus on subject/instructor dropdown")
    print("Starting in 3 seconds....")
    pyautogui.sleep(3)

    eval_form(int(category), subjects)


if __name__ == "__main__":
    main()
