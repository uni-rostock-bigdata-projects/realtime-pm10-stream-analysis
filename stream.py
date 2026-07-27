#!/usr/bin/env python3

import calendar
import logging
import threading
import time
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk

import requests


logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s] (%(threadName)-18s) %(message)s",
)


# =============================================================================
# 1. CONTROL UI
# =============================================================================
class AirQualityDashboard:
    """Tkinter controls for window sizes and fuzzy-join tolerance."""

    def __init__(self, controls):
        self.controls = controls
        self.run_callback = None

        self.root = tk.Tk()
        self.root.title("Air Quality Fuzzy Time Join")
        self.root.geometry("820x465")
        self.root.configure(bg="#121212")
        self.root.resizable(False, False)

        tk.Label(
            self.root,
            text="AIR QUALITY FUZZY TIME JOIN — BERLIN & GÖTTINGEN",
            bg="#121212",
            fg="#FFFFFF",
            font=("Segoe UI", 15, "bold"),
        ).place(x=30, y=20)

        self._create_buffer_panel()
        self._create_control_panel()

        self.status_bar = tk.Label(
            self.root,
            text="Select the parameters and click RUN STREAM.",
            bg="#0D47A1",
            fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            height=2,
        )
        self.status_bar.place(x=30, y=390, width=760)

    def _create_buffer_panel(self):
        frame = tk.Frame(
            self.root,
            bg="#1E1E1E",
            highlightbackground="#333333",
            highlightthickness=1,
        )
        frame.place(x=30, y=70, width=760, height=115)

        tk.Label(
            frame,
            text="SLIDING WINDOW OCCUPANCY",
            bg="#1E1E1E",
            fg="#A0A0A0",
            font=("Segoe UI", 9, "bold"),
        ).place(x=15, y=12)

        self.berlin_buffer_label = tk.Label(
            frame,
            text="Berlin Stream    : [░░░░░░]",
            bg="#1E1E1E",
            fg="#81C784",
            font=("Courier", 10),
        )
        self.berlin_buffer_label.place(x=15, y=43)

        self.goettingen_buffer_label = tk.Label(
            frame,
            text="Göttingen Stream : [░░░░░░]",
            bg="#1E1E1E",
            fg="#FFB74D",
            font=("Courier", 10),
        )
        self.goettingen_buffer_label.place(x=15, y=73)

    def _create_control_panel(self):
        frame = tk.Frame(
            self.root,
            bg="#1E1E1E",
            highlightbackground="#333333",
            highlightthickness=1,
        )
        frame.place(x=30, y=200, width=760, height=165)

        tk.Label(
            frame,
            text="DYNAMIC STREAM CONTROLS",
            bg="#1E1E1E",
            fg="#4FC3F7",
            font=("Segoe UI", 9, "bold"),
        ).place(x=15, y=12)

        self.berlin_window_var = tk.IntVar(
            value=self.controls["berlin_win_size"]
        )
        self.goettingen_window_var = tk.IntVar(
            value=self.controls["goettingen_win_size"]
        )
        self.tolerance_var = tk.IntVar(
            value=self.controls["tolerance_minutes"]
        )

        self._add_slider(
            frame,
            label="Berlin window size",
            variable=self.berlin_window_var,
            minimum=1,
            maximum=4,
            x=15,
        )
        self._add_slider(
            frame,
            label="Göttingen window size",
            variable=self.goettingen_window_var,
            minimum=1,
            maximum=4,
            x=260,
        )
        self._add_slider(
            frame,
            label="Join tolerance (minutes)",
            variable=self.tolerance_var,
            minimum=0,
            maximum=30,
            x=505,
        )

        self.control_status_label = tk.Label(
            frame,
            text=self._control_status_text(),
            bg="#1E1E1E",
            fg="#A0A0A0",
            font=("Courier", 8),
        )
        self.control_status_label.place(x=15, y=125)

        self.run_button = ttk.Button(
            frame,
            text="▶ RUN STREAM",
            command=self._run_clicked,
        )
        self.run_button.place(x=560, y=118, width=180, height=32)

    def _add_slider(self, parent, label, variable, minimum, maximum, x):
        tk.Label(
            parent,
            text=label,
            bg="#1E1E1E",
            fg="#E0E0E0",
            font=("Segoe UI", 9, "bold"),
        ).place(x=x, y=42)

        slider = tk.Scale(
            parent,
            from_=minimum,
            to=maximum,
            orient=tk.HORIZONTAL,
            variable=variable,
            bg="#1E1E1E",
            fg="#E0E0E0",
            highlightthickness=0,
            troughcolor="#2D2D2D",
            activebackground="#4FC3F7",
            length=210,
            command=lambda _value: self.push_controls(),
        )
        slider.place(x=x, y=62)

    def _control_status_text(self):
        return (
            f"Berlin={self.controls['berlin_win_size']} | "
            f"Göttingen={self.controls['goettingen_win_size']} | "
            f"Tolerance={self.controls['tolerance_minutes']} min | "
        )

    def push_controls(self):
        self.controls["berlin_win_size"] = self.berlin_window_var.get()
        self.controls["goettingen_win_size"] = (
            self.goettingen_window_var.get()
        )
        self.controls["tolerance_minutes"] = self.tolerance_var.get()

        self.control_status_label.configure(
            text=self._control_status_text(),
            fg="#81C784",
        )

    def set_run_callback(self, callback):
        self.run_callback = callback

    def _run_clicked(self):
        self.push_controls()

        if self.run_callback is not None:
            self.run_callback()

    def set_running(self, run_number):
        self.run_button.configure(state=tk.DISABLED)
        self.status_bar.configure(
            text=(
                f"RUN #{run_number} ACTIVE — "
                f"Berlin window={self.controls['berlin_win_size']}, "
                f"Göttingen window={self.controls['goettingen_win_size']}, "
                f"tolerance={self.controls['tolerance_minutes']} min"
            ),
            bg="#0D47A1",
        )

    def set_finished(self):
        self.run_button.configure(state=tk.NORMAL)
        self.status_bar.configure(
            text="RUN FINISHED — change the values and run again.",
            bg="#37474F",
        )

    def set_already_running(self):
        self.status_bar.configure(
            text="A stream run is already active. Please wait.",
            bg="#F57C00",
        )

    def update_buffers(
        self,
        berlin_count,
        berlin_capacity,
        goettingen_count,
        goettingen_capacity,
    ):
        self.root.after(
            0,
            lambda: self._render_buffers(
                berlin_count,
                berlin_capacity,
                goettingen_count,
                goettingen_capacity,
            ),
        )

    def _render_buffers(
        self,
        berlin_count,
        berlin_capacity,
        goettingen_count,
        goettingen_capacity,
    ):

        self.berlin_buffer_label.configure(
            text=(
                f"Berlin Window    : "
                f"{berlin_count}/{berlin_capacity} items"
            )
        )

        self.goettingen_buffer_label.configure(
            text=(
                f"Göttingen Window : "
                f"{goettingen_count}/{goettingen_capacity} items"
            )
        )

    @staticmethod
    def _make_bar(count, capacity):
        percent = int((count / capacity) * 100) if capacity else 0
        filled = min(10, int((count / capacity) * 10)) if capacity else 0
        return "█" * filled + "░" * (10 - filled), percent


# =============================================================================
# 2. THREAD-SAFE STREAM
# =============================================================================
class stream:
    def __init__(self, name, winsize):
        self._name = name
        self._winsize = winsize
        self._stream = [None] * winsize
        self._cnt = self._rpos = self._wpos = 0
        self._mutex = threading.Condition()

    def __len__(self):
        return self._winsize

    def __str__(self):
        return (
            "stream(name=%s, q=%s, cnt=%d, rpos=%d, wpos=%d)"
            % (
                self._name,
                str(self._stream),
                self._cnt,
                self._rpos,
                self._wpos,
            )
        )

    def _isfull(self):
        return self._cnt == self._winsize

    def _isempty(self):
        return self._cnt == 0

    def get_cnt(self):
        with self._mutex:
            return self._cnt

    def _enqueue(self, item):
        self._stream[self._wpos] = item
        self._wpos = (self._wpos + 1) % self._winsize
        self._cnt += 1

    def _dequeue(self):
        item = self._stream[self._rpos]
        self._stream[self._rpos] = None
        self._rpos = (self._rpos + 1) % self._winsize
        self._cnt -= 1
        return item

    def put(self, item):
        with self._mutex:
            while self._isfull():
                self._mutex.wait()

            self._enqueue(item)
            self._mutex.notify_all()

    def get(self):
        with self._mutex:
            while self._isempty():
                self._mutex.wait()

            item = self._dequeue()
            self._mutex.notify_all()
            return item

    def inspect(self):
        with self._mutex:
            if self._isempty():
                return None
            return self._stream[self._rpos]


# =============================================================================
# 3. DATA SOURCE
# =============================================================================
class PMDataFountain:
    def __init__(
        self,
        output_stream,
        city,
        latitude,
        longitude,
        years=None,
        months=None,
        max_rows=80,
        time_shift_minutes=0,
    ):
        self.output_stream = output_stream
        self.city = city
        self.latitude = latitude
        self.longitude = longitude
        self.years = years or [2024]
        self.months = months or [9]
        self.max_rows = max_rows
        self.time_shift_minutes = time_shift_minutes

    def run(self):
        emitted_rows = 0

        for year in self.years:
            for month in self.months:
                last_day = calendar.monthrange(year, month)[1]
                start_date = f"{year}-{month:02d}-01"
                end_date = f"{year}-{month:02d}-{last_day:02d}"

                url = (
                    "https://air-quality-api.open-meteo.com/v1/air-quality"
                    f"?latitude={self.latitude}"
                    f"&longitude={self.longitude}"
                    "&hourly=pm10,pm2_5"
                    f"&start_date={start_date}"
                    f"&end_date={end_date}"
                )

                try:
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    data = response.json()

                    times = data["hourly"]["time"]
                    pm10_values = data["hourly"]["pm10"]
                    pm25_values = data["hourly"]["pm2_5"]

                    for timestamp_text, pm10, pm25 in zip(
                        times,
                        pm10_values,
                        pm25_values,
                    ):
                        if pm10 is None:
                            continue

                        timestamp = (
                            datetime.fromisoformat(timestamp_text)
                            + timedelta(minutes=self.time_shift_minutes)
                        )

                        self.output_stream.put(
                            (timestamp, self.city, pm10, pm25)
                        )
                        emitted_rows += 1

                        if (
                            self.max_rows is not None
                            and emitted_rows >= self.max_rows
                        ):
                            self.output_stream.put(
                                ("END", self.city, None, None)
                            )
                            return

                        time.sleep(0.3)

                except (
                    requests.RequestException,
                    KeyError,
                    ValueError,
                ) as error:
                    logging.error(
                        "Failed to load data for %s: %s",
                        self.city,
                        error,
                    )

        self.output_stream.put(("END", self.city, None, None))


# =============================================================================
# 4. FUZZY TIME JOIN
# =============================================================================
def format_window(window):
    return "[" + ", ".join(
        f"{item[0].strftime('%H:%M')}:{item[2]:.1f}"
        for item in window
    ) + "]"


def emit_join_if_matching(
    berlin_tuple,
    goettingen_tuple,
    output_stream,
    tolerance_minutes,
    emitted_pairs,
    berlin_window,
    goettingen_window,
):
    berlin_ts, _, berlin_pm10, berlin_pm25 = berlin_tuple
    goettingen_ts, _, goettingen_pm10, goettingen_pm25 = (
        goettingen_tuple
    )

    time_difference = abs(
        (berlin_ts - goettingen_ts).total_seconds()
    ) / 60

    if time_difference > tolerance_minutes:
        return

    pair_key = (berlin_ts, goettingen_ts)

    if pair_key in emitted_pairs:
        return

    emitted_pairs.add(pair_key)

    output_stream.put(
        (
            berlin_ts,
            goettingen_ts,
            berlin_pm10,
            goettingen_pm10,
            berlin_pm25,
            goettingen_pm25,
            time_difference,
            abs(berlin_pm10 - goettingen_pm10),
            format_window(berlin_window),
            format_window(goettingen_window),
        )
    )


def fuzzy_time_join(
    berlin_stream,
    goettingen_stream,
    output_stream,
    controls,
    dashboard,
):
    berlin_window = []
    goettingen_window = []
    emitted_pairs = set()

    while True:
        # Read one tuple from each stream as one processing step.
        berlin_item = berlin_stream.get()
        goettingen_item = goettingen_stream.get()

        # Finish when either input reaches its end marker.
        if (
            berlin_item[0] == "END"
            or goettingen_item[0] == "END"
        ):
            output_stream.put(
                (
                    "END",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            )
            break

        # Add one new item to each logical window.
        berlin_window.append(berlin_item)
        goettingen_window.append(goettingen_item)

        # Apply the current dynamic window sizes.
        berlin_window[:] = berlin_window[
            -controls["berlin_win_size"]:
        ]

        goettingen_window[:] = goettingen_window[
            -controls["goettingen_win_size"]:
        ]

        dashboard.update_buffers(
            len(berlin_window),
            controls["berlin_win_size"],
            len(goettingen_window),
            controls["goettingen_win_size"],
        )

        # Join the newly received Berlin and Göttingen records.
        emit_join_if_matching(
            berlin_item,
            goettingen_item,
            output_stream,
            controls["tolerance_minutes"],
            emitted_pairs,
            berlin_window,
            goettingen_window,
        )

        time.sleep(0.01)
# =============================================================================
# 5. SINK
# =============================================================================
def air_quality_sink(
    input_stream,
    berlin_stream,
    goettingen_stream,
    dashboard,
    on_complete,
):
    print("\nAir Quality Fuzzy Join with Dynamic Sliding Windows")
    print("-" * 220)
    print(
        f"{'Berlin Time':<20} "
        f"{'Göttingen Time':<20} "
        f"{'Time Diff':<10} "
        f"{'Berlin PM10':<12} "
        f"{'Göttingen PM10':<16} "
        f"{'PM10 Diff':<10} "
        f"{'Berlin Window':<65} "
        f"{'Göttingen Window'}"
    )
    print("-" * 220)

    while True:
        item = input_stream.get()

        if item[0] == "END":
            print("-" * 220)
            print("End of stream.")
            dashboard.root.after(0, on_complete)
            break

        (
            berlin_ts,
            goettingen_ts,
            berlin_pm10,
            goettingen_pm10,
            _berlin_pm25,
            _goettingen_pm25,
            time_difference,
            pm10_difference,
            berlin_window_text,
            goettingen_window_text,
        ) = item

        print(
            f"{str(berlin_ts):<20} "
            f"{str(goettingen_ts):<20} "
            f"{time_difference:<10.2f} "
            f"{berlin_pm10:<12.2f} "
            f"{goettingen_pm10:<16.2f} "
            f"{pm10_difference:<10.2f} "
            f"{berlin_window_text:<65} "
            f"{goettingen_window_text}"
        )


# =============================================================================
# 6. APPLICATION LIFECYCLE
# =============================================================================
if __name__ == "__main__":
    controls = {
        "berlin_win_size": 4,
        "goettingen_win_size": 4,
        "tolerance_minutes": 15,
        "goettingen_offset_minutes": 10,
    }

    dashboard = AirQualityDashboard(controls)

    run_state = {
        "running": False,
        "run_number": 0,
    }

    def mark_run_finished():
        run_state["running"] = False
        dashboard.set_finished()

    def start_stream_run():
        dashboard.push_controls()

        if run_state["running"]:
            dashboard.set_already_running()
            return

        run_state["running"] = True
        run_state["run_number"] += 1
        current_run = run_state["run_number"]

        dashboard.set_running(current_run)

        print("\n" + "=" * 110)
        print(f"STARTING STREAM RUN #{current_run}")
        print(
            f"Berlin window={controls['berlin_win_size']} | "
            f"Göttingen window={controls['goettingen_win_size']} | "
            f"Tolerance={controls['tolerance_minutes']} min | "
            f"Göttingen artificial offset="
            f"{controls['goettingen_offset_minutes']} min"
        )
        print("=" * 110)

        # Fresh streams are created for every run.
        berlin_stream = stream("Berlin source stream", 10)
        goettingen_stream = stream("Göttingen source stream", 10)
        joined_stream = stream("Joined output stream", 10)

        berlin_source = PMDataFountain(
            output_stream=berlin_stream,
            city="Berlin",
            latitude=52.52,
            longitude=13.41,
            years=[2024],
            months=[9],
            max_rows=80,
            time_shift_minutes=0,
        )

        goettingen_source = PMDataFountain(
            output_stream=goettingen_stream,
            city="Göttingen",
            latitude=51.54,
            longitude=9.93,
            years=[2024],
            months=[9],
            max_rows=80,
            time_shift_minutes=controls["tolerance_minutes"],        
        )

        threads = [
            threading.Thread(
                name=f"BerlinSource-{current_run}",
                target=berlin_source.run,
                daemon=True,
            ),
            threading.Thread(
                name=f"GoettingenSource-{current_run}",
                target=goettingen_source.run,
                daemon=True,
            ),
            threading.Thread(
                name=f"FuzzyTimeJoin-{current_run}",
                target=fuzzy_time_join,
                args=(
                    berlin_stream,
                    goettingen_stream,
                    joined_stream,
                    controls,
                    dashboard
                ),
                daemon=True,
            ),
            threading.Thread(
                name=f"AirQualitySink-{current_run}",
                target=air_quality_sink,
                args=(
                    joined_stream,
                    berlin_stream,
                    goettingen_stream,
                    dashboard,
                    mark_run_finished,
                ),
                daemon=True,
            ),
        ]

        for thread in threads:
            thread.start()

    dashboard.set_run_callback(start_stream_run)
    dashboard.root.mainloop()
