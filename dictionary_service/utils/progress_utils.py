def calculate_overall_progress(total_progress, max_progress, precision=3):
    """
    Вычисляет общий процент прогресса.

    :param total_progress: Суммарный прогресс.
    :param max_progress: Максимально возможный прогресс.
    :param precision: Число знаков после запятой.
    :return: Процент прогресса, округленный до заданной точности.
    """
    if max_progress <= 0:
        return 0
    return round((total_progress / max_progress) * 100, precision)
