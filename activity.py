def calculate_avg(times):
    return round(sum(times) / len(times), 2)  # Round to 2 decimal places


def fcfs_scheduling(processes, context_switch=0):
    print("\n--- FCFS Scheduling ---")
    n = len(processes)
    completion_time = [0] * n
    waiting_time = [0] * n
    turnaround_time = [0] * n

    # Calculate Completion Time
    current_time = 0
    for i, (arrival_time, burst_time) in enumerate(processes):
        if i > 0:  # Add context switch after the first process
            current_time += context_switch
        current_time = max(current_time, arrival_time) + burst_time
        completion_time[i] = current_time

    # Calculate Waiting Time and Turnaround Time
    for i, (arrival_time, burst_time) in enumerate(processes):
        turnaround_time[i] = completion_time[i] - arrival_time
        waiting_time[i] = turnaround_time[i] - burst_time

    avg_waiting = calculate_avg(waiting_time)
    avg_turnaround = calculate_avg(turnaround_time)

    print(f"Waiting Times: {list(map(lambda x: round(x, 2), waiting_time))}")
    print(f"Turnaround Times: {list(map(lambda x: round(x, 2), turnaround_time))}")
    print(f"Average Waiting Time: {avg_waiting}")
    print(f"Average Turnaround Time: {avg_turnaround}")


def sjn_scheduling(processes, context_switch=0):
    print("\n--- SJN Scheduling ---")
    n = len(processes)
    processes = sorted(processes, key=lambda x: (x[0], x[1]))  # Sort by arrival, then burst
    completed = [False] * n
    current_time = 0
    waiting_time = [0] * n
    turnaround_time = [0] * n

    for _ in range(n):
        # Select the shortest job available at current time
        available_processes = [(i, bt) for i, (at, bt) in enumerate(processes) if at <= current_time and not completed[i]]
        if not available_processes:
            current_time += 1
            continue

        shortest_job = min(available_processes, key=lambda x: x[1])[0]
        at, bt = processes[shortest_job]
        completed[shortest_job] = True

        if any(completed):  # Add context switch after the first process
            current_time += context_switch

        current_time += bt
        turnaround_time[shortest_job] = current_time - at
        waiting_time[shortest_job] = turnaround_time[shortest_job] - bt

    avg_waiting = calculate_avg(waiting_time)
    avg_turnaround = calculate_avg(turnaround_time)

    print(f"Waiting Times: {list(map(lambda x: round(x, 2), waiting_time))}")
    print(f"Turnaround Times: {list(map(lambda x: round(x, 2), turnaround_time))}")
    print(f"Average Waiting Time: {avg_waiting}")
    print(f"Average Turnaround Time: {avg_turnaround}")


def round_robin_scheduling(processes, time_quantum, context_switch=0):
    print("\n--- Round Robin Scheduling ---")
    n = len(processes)
    burst_times = [bt for _, bt in processes]
    remaining_times = burst_times[:]
    arrival_times = [at for at, _ in processes]

    current_time = 0
    waiting_time = [0] * n
    turnaround_time = [0] * n
    queue = []
    completed = [False] * n

    # Initially add processes that have arrived
    while True:
        # Add processes to the queue
        for i, at in enumerate(arrival_times):
            if at <= current_time and not completed[i] and i not in queue:
                queue.append(i)

        if not queue:
            current_time += 1
            continue

        # Process the first item in the queue
        idx = queue.pop(0)
        if remaining_times[idx] <= time_quantum:
            current_time += remaining_times[idx]
            remaining_times[idx] = 0
            completed[idx] = True
            turnaround_time[idx] = current_time - arrival_times[idx]
            waiting_time[idx] = turnaround_time[idx] - burst_times[idx]
        else:
            current_time += time_quantum
            remaining_times[idx] -= time_quantum
            queue.append(idx)

        # Add context switch time after every quantum
        current_time += context_switch

        if all(completed):
            break

    avg_waiting = calculate_avg(waiting_time)
    avg_turnaround = calculate_avg(turnaround_time)

    print(f"Waiting Times: {list(map(lambda x: round(x, 2), waiting_time))}")
    print(f"Turnaround Times: {list(map(lambda x: round(x, 2), turnaround_time))}")
    print(f"Average Waiting Time: {avg_waiting}")
    print(f"Average Turnaround Time: {avg_turnaround}")


def rmt_scheduling(processes, context_switch=0):
    print("\n--- RMT Scheduling ---")
    n = len(processes)
    processes = sorted(processes, key=lambda x: x[1])  # Sort by burst time (priority)
    completed = [False] * n
    current_time = 0
    waiting_time = [0] * n
    turnaround_time = [0] * n

    for _ in range(n):
        # Select the highest-priority (shortest burst time) process available
        available_processes = [(i, bt) for i, (at, bt) in enumerate(processes) if at <= current_time and not completed[i]]
        if not available_processes:
            current_time += 1
            continue

        highest_priority = min(available_processes, key=lambda x: x[1])[0]
        at, bt = processes[highest_priority]
        completed[highest_priority] = True

        if any(completed):  # Add context switch after the first process
            current_time += context_switch

        current_time += bt
        turnaround_time[highest_priority] = current_time - at
        waiting_time[highest_priority] = turnaround_time[highest_priority] - bt

    avg_waiting = calculate_avg(waiting_time)
    avg_turnaround = calculate_avg(turnaround_time)

    print(f"Waiting Times: {list(map(lambda x: round(x, 2), waiting_time))}")
    print(f"Turnaround Times: {list(map(lambda x: round(x, 2), turnaround_time))}")
    print(f"Average Waiting Time: {avg_waiting}")
    print(f"Average Turnaround Time: {avg_turnaround}")


# Input Data: Arrival Time and CPU Scheduling Time
processes = [
    (0, 6), (3, 2), (5, 1), (9, 7), (10, 5),
    (12, 3), (14, 4), (16, 5), (17, 7), (19, 2), (20, 6)
]

context_switch_time = 0.4  # Context switching time in milliseconds

# Run FCFS, SJN, RMT, and Round Robin scheduling with context switch time
fcfs_scheduling(processes, context_switch=context_switch_time)
sjn_scheduling(processes, context_switch=context_switch_time)
rmt_scheduling(processes, context_switch=context_switch_time)
round_robin_scheduling(processes, time_quantum=4, context_switch=context_switch_time)
