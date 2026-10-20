def calculate_student_grade(marks):
    """Calculate a student's grade from marks."""
    if marks >= 80:
        return "A"
    if marks >= 60:
        return "B"
    return "C"