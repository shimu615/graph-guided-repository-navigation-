
"""Generate a student report using the grade calculation module."""

from student import calculate_student_grade


def generate_report(student_name, marks):
    """Generate a report with the student's calculated grade."""
    grade = calculate_student_grade(marks)
    return f"{student_name}: {grade}"
