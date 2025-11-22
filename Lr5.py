import random
import time
import logging
from dataclasses import dataclass
from collections import OrderedDict

logger = logging.getLogger("sorts")


def setup_logging(level="WARNING"):
    numeric = getattr(logging, level.upper(), logging.WARNING)
    logging.basicConfig(level=numeric, format="%(levelname)s:%(message)s")
    logger.setLevel(numeric)


@dataclass
class SortResult:
    algorithm: str
    time_ms: float
    comparisons: int
    swaps_or_writes: int
    iterations: int


@dataclass
class Counter:
    comparisons = 0
    swaps_or_writes = 0
    iterations = 0


def instrumented_compare(a, b, counter):
    counter.comparisons += 1
    return (a > b) - (a < b)


def log_state(name, arr, counter, message=""):
    logger.debug(
        f"[{name}] {message} | state={arr} | cmp={counter.comparisons}, writes={counter.swaps_or_writes}, iters={counter.iterations}"
    )


def _check_input_numbers(arr, logger_name):
    for x in arr:
        if not isinstance(x, (int, float)):
            logger.error(
                f"Некорректный элемент: {x} ({type(x)}) в алгоритме {logger_name}"
            )
            raise TypeError(f"Элемент {x} недопустимого типа: {type(x)}")


def bubble_sort(arr, logger_name="Bubble"):
    _check_input_numbers(arr, logger_name)
    a = arr.copy()
    c = Counter()
    n = len(a)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            c.iterations += 1
            if instrumented_compare(a[j], a[j + 1], c) > 0:
                a[j], a[j + 1] = a[j + 1], a[j]
                c.swaps_or_writes += 3
                swapped = True
                log_state(logger_name, a, c, f"swap {j}<->{j+1}")
        if not swapped:
            break
    return a, c


def selection_sort(arr, logger_name="Selection"):
    _check_input_numbers(arr, logger_name)
    a = arr.copy()
    c = Counter()
    n = len(a)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            c.iterations += 1
            if instrumented_compare(a[j], a[min_idx], c) < 0:
                min_idx = j
        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]
            c.swaps_or_writes += 3
            log_state(logger_name, a, c, f"swap {i}<->{min_idx}")
    return a, c


def insertion_sort(arr, logger_name="Insertion"):
    _check_input_numbers(arr, logger_name)
    a = arr.copy()
    c = Counter()
    for i in range(1, len(a)):
        key = a[i]
        c.swaps_or_writes += 1
        j = i - 1
        while j >= 0 and instrumented_compare(a[j], key, c) > 0:
            a[j + 1] = a[j]
            c.swaps_or_writes += 1
            j -= 1
            c.iterations += 1
        a[j + 1] = key
        c.swaps_or_writes += 1
        log_state(logger_name, a, c, f"insert key {i}->{j+1}")
    return a, c


def merge_sort(arr, logger_name="Merge"):
    _check_input_numbers(arr, logger_name)
    a = arr.copy()
    c = Counter()

    def _merge_sort(lst):
        if len(lst) <= 1:
            return lst
        mid = len(lst) // 2
        left = _merge_sort(lst[:mid])
        right = _merge_sort(lst[mid:])
        return _merge(left, right)

    def _merge(left, right):
        res = []
        i = j = 0
        while i < len(left) and j < len(right):
            c.iterations += 1
            if instrumented_compare(left[i], right[j], c) <= 0:
                res.append(left[i])
                c.swaps_or_writes += 1
                i += 1
            else:
                res.append(right[j])
                c.swaps_or_writes += 1
                j += 1
        while i < len(left):
            res.append(left[i])
            c.swaps_or_writes += 1
            i += 1
        while j < len(right):
            res.append(right[j])
            c.swaps_or_writes += 1
            j += 1
        log_state(logger_name, res, c, "merge chunk")
        return res

    return _merge_sort(a), c


def quick_sort(arr, logger_name="Quick"):
    _check_input_numbers(arr, logger_name)
    a = arr.copy()
    c = Counter()

    def _qs(lst):
        if len(lst) <= 1:
            return lst
        first = lst[0]
        mid = lst[len(lst) // 2]
        last = lst[-1]
        pivot = sorted([first, mid, last])[1]
        less, equal, greater = [], [], []
        for x in lst:
            c.iterations += 1
            comp = instrumented_compare(x, pivot, c)
            if comp < 0:
                less.append(x)
                c.swaps_or_writes += 1
            elif comp > 0:
                greater.append(x)
                c.swaps_or_writes += 1
            else:
                equal.append(x)
                c.swaps_or_writes += 1
        log_state(logger_name, lst, c, f"pivot={pivot}")
        return _qs(less) + equal + _qs(greater)

    return _qs(a), c


def heap_sort(arr, logger_name="Heap"):
    _check_input_numbers(arr, logger_name)
    a = arr.copy()
    c = Counter()
    n = len(a)

    def heapify(n_, i):
        largest = i
        l = 2 * i + 1
        r = 2 * i + 2
        if l < n_ and instrumented_compare(a[l], a[largest], c) > 0:
            largest = l
        if r < n_ and instrumented_compare(a[r], a[largest], c) > 0:
            largest = r
        if largest != i:
            a[i], a[largest] = a[largest], a[i]
            c.swaps_or_writes += 3
            c.iterations += 1
            heapify(n_, largest)

    for i in range(n // 2 - 1, -1, -1):
        heapify(n, i)
    for i in range(n - 1, 0, -1):
        a[i], a[0] = a[0], a[i]
        c.swaps_or_writes += 3
        heapify(i, 0)
        log_state(logger_name, a, c, f"move max->{i}")
    return a, c


ALGORITHMS = {
    "Bubble": bubble_sort,
    "Selection": selection_sort,
    "Insertion": insertion_sort,
    "Merge": merge_sort,
    "Quick": quick_sort,
    "Heap": heap_sort,
}


def run_benchmark_one(data):
    print(f"\nИсходный список:\n{data}\n")
    results = []
    for name, algo in ALGORITHMS.items():
        arr = data.copy()
        start = time.perf_counter()
        sorted_arr, counter = algo(arr)
        elapsed = (time.perf_counter() - start) * 1000.0
        assert sorted_arr == sorted(data), f"{name} failed"
        results.append(
            SortResult(
                name,
                elapsed,
                counter.comparisons,
                counter.swaps_or_writes,
                counter.iterations,
            )
        )
        print(
            f"{name:<10}  {elapsed:7.3f} ms  cmp={counter.comparisons:<6}  writes={counter.swaps_or_writes:<6}  iters={counter.iterations:<6}"
        )
    return results


def first_letters_key(full_name):
    parts = full_name.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    return (first[:1], last[:1])


def sort_people_examples():
    people = {
        "Алексей Смирнов": 34,
        "Ирина Кузнецова": 28,
        "Дмитрий Иванов": 42,
        "Мария Петрова": 25,
        "Сергей Волков": 31,
        "Анна Соколова": 29,
        "Екатерина Морозова": 37,
        "Павел Новиков": 22,
        "Николай Фёдоров": 45,
        "Ольга Васильева": 33,
        "Татьяна Орлова": 27,
        "Виктор Киселёв": 39,
        "Юлия Александрова": 26,
        "Григорий Лебедев": 41,
    }
    by_age = OrderedDict(sorted(people.items(), key=lambda kv: kv[1]))
    by_initials = OrderedDict(
        sorted(people.items(), key=lambda kv: first_letters_key(kv[0]))
    )
    return people, by_age, by_initials


def main():
    setup_logging("WARNING")
    data = [random.randint(0, 100) for _ in range(20)]
    run_benchmark_one(data)
    bad_data = [1, "a", 3]
    print("\n--- Тест сортировок на некорректных данных ---")
    print(bad_data)
    for name, algo in ALGORITHMS.items():
        try:
            algo(bad_data)
        except Exception as e:
            print(f"{name}: ошибка: {e}")
    people, by_age, by_init = sort_people_examples()
    print("\n--- Сортировка словаря по возрасту ---")
    for k, v in by_age.items():
        print(f"{k:<25} {v}")
    print("\n--- Сортировка словаря по первым буквам имени и фамилии ---")
    for k, v in by_init.items():
        ini = "".join(first_letters_key(k))
        print(f"{k:<25} {v:>2} | инициалы: {ini}")


main()
