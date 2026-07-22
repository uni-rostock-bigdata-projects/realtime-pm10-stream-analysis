import threading
import time
import random
import logging
import requests
import calendar
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk

logging.basicConfig(level=logging.WARNING)


# =================================================================================================
# 1. ENHANCED AIR QUALITY DASHBOARD UI (STORM TOPOLOGY INTERFACE)
# =================================================================================================
class AirQualityDash:
    def __init__(self, topology_controls=None):
        # @@@ Shared control dictionary.
        # @@@ The GUI sliders update these values while the topology is running.
        self.controls = topology_controls or {
            "berlin_win_size": 4,
            "goettingen_win_size": 4,
            "tolerance_minutes": 15
        }

        self.root = tk.Tk()
        self.root.title("Big Data Processing Engine - Storm Topology Interface")
        self.root.configure(bg="#121212")
        self.root.geometry("780x490")
        self.root.resizable(False, False)

        tk.Label(
            self.root,
            text="REAL-TIME URBAN AIR QUALITY TRACKER (Berlin & Goettingen)",
            bg="#121212",
            fg="#FFFFFF",
            font=("Segoe UI", 14, "bold")
        ).place(x=30, y=20)
    
        # --- CARD 2: Data Pipeline Buffer Load ---
        matrix_frame = tk.Frame(
            self.root,
            bg="#1E1E1E",
            bd=1,
            relief="solid",
            highlightbackground="#333333",
            highlightthickness=1
        )
        matrix_frame.place(x=30, y=70, width=720, height=120)

        tk.Label(
            matrix_frame,
            text="⚙️ DATA PIPELINE BUFFER LOAD",
            bg="#1E1E1E",
            fg="#A0A0A0",
            font=("Segoe UI", 9, "bold")
        ).place(x=15, y=15)

        self.lbl_buf1 = tk.Label(
            matrix_frame,
            text="Berlin Stream    : [░░░░░░░░░░] 0%",
            bg="#1E1E1E",
            fg="#B0BEC5",
            font=("Segoe UI Mono", 10)
        )
        self.lbl_buf1.place(x=15, y=45)

        self.lbl_buf2 = tk.Label(
            matrix_frame,
            text="Goettingen Stream: [░░░░░░░░░░] 0%",
            bg="#1E1E1E",
            fg="#FFB74D",
            font=("Segoe UI Mono", 10)
        )
        self.lbl_buf2.place(x=15, y=75)

        # --- CARD 3: LIVE SLIDING WINDOW CONTROLS PANEL ---
        control_frame = tk.Frame(
            self.root,
            bg="#1E1E1E",
            bd=1,
            relief="solid",
            highlightbackground="#333333",
            highlightthickness=1
        )
        control_frame.place(x=30, y=205, width=720, height=125)

        tk.Label(
            control_frame,
            text="🎛️ DYNAMIC STREAM SLIDING WINDOW ARCHITECTURE",
            bg="#1E1E1E",
            fg="#4FC3F7",
            font=("Segoe UI", 9, "bold")
        ).place(x=15, y=10)

        # @@@ Berlin dynamic window-size slider.
        tk.Label(
            control_frame,
            text="Berlin Window Size:",
            bg="#1E1E1E",
            fg="#E0E0E0",
            font=("Segoe UI", 9, "bold")
        ).place(x=15, y=40)

        self.b_win_var = tk.IntVar(value=self.controls["berlin_win_size"])
        self.b_slider = tk.Scale(
            control_frame,
            from_=1,
            to=4,
            orient=tk.HORIZONTAL,
            variable=self.b_win_var,
            bg="#1E1E1E",
            fg="#E0E0E0",
            highlightthickness=0,
            troughcolor="#2D2D2D",
            activebackground="#81C784",
            length=180,
            command=lambda x: self._push_controls()
        )
        self.b_slider.place(x=15, y=60)

        # @@@ Goettingen dynamic window-size slider.
        tk.Label(
            control_frame,
            text="Goettingen Window Size:",
            bg="#1E1E1E",
            fg="#E0E0E0",
            font=("Segoe UI", 9, "bold")
        ).place(x=240, y=40)

        self.g_win_var = tk.IntVar(value=self.controls["goettingen_win_size"])
        self.g_slider = tk.Scale(
            control_frame,
            from_=1,
            to=4,
            orient=tk.HORIZONTAL,
            variable=self.g_win_var,
            bg="#1E1E1E",
            fg="#E0E0E0",
            highlightthickness=0,
            troughcolor="#2D2D2D",
            activebackground="#FFB74D",
            length=180,
            command=lambda x: self._push_controls()
        )
        self.g_slider.place(x=240, y=60)

        # @@@ Fuzzy join tolerance slider.
        tk.Label(
            control_frame,
            text="Fuzzy Time Delta:",
            bg="#1E1E1E",
            fg="#E0E0E0",
            font=("Segoe UI", 9, "bold")
        ).place(x=480, y=40)

        self.tol_var = tk.IntVar(value=self.controls["tolerance_minutes"])
        self.tol_slider = tk.Scale(
            control_frame,
            from_=0,
            to=30,
            orient=tk.HORIZONTAL,
            variable=self.tol_var,
            bg="#1E1E1E",
            fg="#E0E0E0",
            highlightthickness=0,
            troughcolor="#2D2D2D",
            activebackground="#4FC3F7",
            length=200,
            command=lambda x: self._push_controls()
        )
        self.tol_slider.place(x=480, y=60)

        self.lbl_control_status = tk.Label(
            control_frame,
            text="Sliding adjustments synchronized with Storm-style Bolts in real time.",
            bg="#1E1E1E",
            fg="#A0A0A0",
            font=("Segoe UI Mono", 8)
        )
        self.lbl_control_status.place(x=15, y=105)
        
        self.run_callback = None
        self.btn_run = ttk.Button(
			control_frame,
			text="▶ RUN STREAM",
			command=self._run_clicked
		)
        self.btn_run.place(x=500, y=5, width=200, height=30)


        self.alarm_bar = tk.Label(
            self.root,
            text="INITIALIZING STORM-STYLE TOPOLOGY LIFECYCLE ENGINE...",
            bg="#0D47A1",
            fg="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            height=2
        )
        self.alarm_bar.place(x=30, y=395, width=720)

    def _push_controls(self):
        try:
            # @@@ These values are changed live by the sliders.
            self.controls["berlin_win_size"] = self.b_win_var.get()
            self.controls["goettingen_win_size"] = self.g_win_var.get()
            self.controls["tolerance_minutes"] = self.tol_var.get()

            status_text = (
                f"Live Window Adjusted! "
                f"Berlin Max: {self.controls['berlin_win_size']} | "
                f"Goettingen Max: {self.controls['goettingen_win_size']} | "
                f"Join Tolerance: {self.controls['tolerance_minutes']} mins"
            )
            self.lbl_control_status.configure(text=status_text, fg="#81C784")
        except Exception:
            pass

    def update_ui(self, ts1, ts2, pm10_1, pm10_2, time_diff, pm10_diff, b_win, g_win, b1_cnt, b2_cnt):
        try:
            self.root.after(
                0,
                lambda: self._safe_ui_render(
                    ts1, ts2, pm10_1, pm10_2, time_diff,
                    pm10_diff, b_win, g_win, b1_cnt, b2_cnt
                )
            )
        except Exception:
            pass

    def _safe_ui_render(self, ts1, ts2, pm10_1, pm10_2, time_diff, pm10_diff, b_win, g_win, b1_cnt, b2_cnt):
        try:
            if ts1 == "END":
                self.alarm_bar.configure(
                    text="🏁 STORM-STYLE TOPOLOGY TERMINATED: END OF COMPONENT LIFECYCLE",
                    bg="#37474F"
                )
                return

            # @@@ Update pipeline buffer load first.
            # @@@ This part does not depend on timestamp labels.
            bar1_fill = int((b1_cnt / 10) * 10)
            bar1_txt = "█" * bar1_fill + "░" * (10 - bar1_fill)
            self.lbl_buf1.configure(
                text=f"Berlin Stream    : [{bar1_txt}] {int((b1_cnt / 10) * 100)}%"
            )

            bar2_fill = int((b2_cnt / 10) * 10)
            bar2_txt = "█" * bar2_fill + "░" * (10 - bar2_fill)
            self.lbl_buf2.configure(
                text=f"Goettingen Stream: [{bar2_txt}] {int((b2_cnt / 10) * 100)}%"
            )

            # @@@ Only update these labels if they exist in the UI.
            if hasattr(self, "lbl_ts1"):
                self.lbl_ts1.configure(text=f"⏱️ Berlin Time : {ts1.strftime('%Y-%m-%d %H:%M')}")

            if hasattr(self, "lbl_ts2"):
                self.lbl_ts2.configure(text=f"⏱️ Goett. Time : {ts2.strftime('%Y-%m-%d %H:%M')}")

            if hasattr(self, "lbl_pm10_chip"):
                self.lbl_pm10_chip.configure(text=f"🟠 Berlin PM10: {pm10_1:.1f}")

            if hasattr(self, "lbl_pm25_chip"):
                self.lbl_pm25_chip.configure(text=f"🔴 Goett. PM10: {pm10_2:.1f}")

            if hasattr(self, "lbl_trend_chip"):
                self.lbl_trend_chip.configure(text=f"🌟 PM10 DIFF: {pm10_diff:.2f} μg/m³")

            if hasattr(self, "lbl_time_diff_chip"):
                self.lbl_time_diff_chip.configure(text=f"⏳ DELTA: {time_diff:.0f}m")

            if hasattr(self, "lbl_window_timeline"):
                self.lbl_window_timeline.configure(text=f"Berlin Window: {b_win}")

            if hasattr(self, "lbl_g_window_timeline"):
                self.lbl_g_window_timeline.configure(text=f"Goett. Window: {g_win}")

        except Exception as e:
            print("UI update error:", e)

    # @@@ Allows the main program to connect the Run button to the topology starter.
    def set_run_callback(self, callback):
        self.run_callback = callback

    # @@@ Called when the Run button is clicked.
    def _run_clicked(self):
        self._push_controls()

        self.alarm_bar.configure(
            text="▶ STARTING NEW STORM-STYLE TOPOLOGY RUN...",
            bg="#0D47A1"
        )

        if self.run_callback is not None:
            self.run_callback()
# =================================================================================================
# 2. THREAD-SAFE STREAM KERNEL
# =================================================================================================
class stream:
    def __init__(self, name, winsize):
        self._name = name
        self._winsize = winsize
        self._stream = [None] * winsize
        self._cnt = self._rpos = self._wpos = 0
        self._mutex = threading.Condition()

    def __len__(self):
        return len(self._stream)

    def __str__(self):
        return "stream(name=%s, q=%s, cnt=%d, rpos=%d, wpos=%d)" % (
            self._name,
            str(self._stream),
            self._cnt,
            self._rpos,
            self._wpos
        )

    def _isfull(self):
        return self._rpos == self._wpos and self._cnt == self._winsize

    def _isempty(self):
        return self._rpos == self._wpos and self._cnt == 0

    def get_cnt(self):
        return self._cnt

    def _enqueue(self, t):
        self._cnt += 1
        self._stream[self._wpos] = t

        if self._wpos + 1 == self._winsize:
            self._wpos = 0
        else:
            self._wpos += 1

    def _dequeue(self):
        t = self._stream[self._rpos]
        self._stream[self._rpos] = None

        if self._rpos + 1 == self._winsize:
            self._rpos = 0
        else:
            self._rpos += 1

        self._cnt -= 1
        return t

    def put(self, t):
        self._mutex.acquire()

        while self._isfull():
            self._mutex.wait()

        self._enqueue(t)
        self._mutex.notify()
        self._mutex.release()

    def get(self):
        self._mutex.acquire()

        while self._isempty():
            self._mutex.wait()

        t = self._dequeue()
        self._mutex.notify()
        self._mutex.release()

        return t

    def inspect(self):
        self._mutex.acquire()

        if self._isempty():
            t = None
        else:
            t = self._stream[self._rpos]

        self._mutex.release()
        return t


# =================================================================================================
# 3. APACHE STORM-STYLE COMPONENTS: SPOUT / BOLT / SINK
# =================================================================================================
class PMDataSpout:
    def __init__(
        self,
        output_stream,
        selected_city,
        lat,
        lon,
        max_rows=80,
        time_shift_minutes=0,
        shared_controls=None,
        use_dynamic_time_shift=False
    ):
        self.output_stream = output_stream
        self.selected_city = selected_city
        self.lat = lat
        self.lon = lon
        self.max_rows = max_rows
        self.time_shift_minutes = time_shift_minutes

        # @@@ Optional shared controls from the GUI.
        self.shared_controls = shared_controls

        # @@@ If True, this spout uses tolerance_minutes as its time shift.
        self.use_dynamic_time_shift = use_dynamic_time_shift

    def run(self):
        years = [2020, 2021, 2022, 2023, 2024, 2025]
        months = [9, 12]
        emitted_rows = 0

        for year in years:
            for month_value in months:
                last_day = calendar.monthrange(year, month_value)[1]
                start_date = f"{year}-{month_value:02d}-01"
                end_date = f"{year}-{month_value:02d}-{last_day}"

                url = (
                    "https://air-quality-api.open-meteo.com/v1/air-quality?"
                    f"latitude={self.lat}&longitude={self.lon}"
                    "&hourly=pm10,pm2_5"
                    f"&start_date={start_date}"
                    f"&end_date={end_date}"
                )

                try:
                    data = requests.get(url).json()
                    times = data["hourly"]["time"]
                    pm10_values = data["hourly"]["pm10"]
                    pm25_values = data["hourly"]["pm2_5"]

                    for i in range(len(times)):
                        timestamp = times[i]
                        pm10 = pm10_values[i]
                        pm25 = pm25_values[i]

                        if pm10 is None:
                            continue

                        ts = datetime.fromisoformat(timestamp)
                        if self.use_dynamic_time_shift and self.shared_controls is not None:
                            dynamic_shift = self.shared_controls["tolerance_minutes"]
                        else:
                            dynamic_shift = self.time_shift_minutes
                        ts = ts + timedelta(minutes=dynamic_shift)

                        tuple_data = (ts, self.selected_city, pm10, pm25)

                        # @@@ Storm-style emit from spout into stream.
                        self.output_stream.put(tuple_data)

                        emitted_rows += 1

                        if self.max_rows is not None and emitted_rows >= self.max_rows:
                            self.output_stream.put(("END", self.selected_city, None, None))
                            return

                        time.sleep(0.05)

                except Exception:
                    pass

        self.output_stream.put(("END", self.selected_city, None, None))


def format_window(window):
    return "[" + ", ".join(
        f"{item[0].strftime('%H:%M')}:{item[2]:.1f}"
        for item in window
    ) + "]"


class FuzzyJoinBolt:
    def __init__(
        self,
        input_stream_1,
        input_stream_2,
        output_stream,
        shared_controls
    ):
        self.input_stream_1 = input_stream_1
        self.input_stream_2 = input_stream_2
        self.output_stream = output_stream
        self.controls = shared_controls

        self.berlin_window = []
        self.goettingen_window = []

        # Prevent the same Berlin–Goettingen pair being emitted twice.
        self.emitted_pairs = set()

    def _trim_windows(self):
        """Apply the current window sizes selected in the GUI."""

        while len(self.berlin_window) > self.controls["berlin_win_size"]:
            self.berlin_window.pop(0)

        while len(self.goettingen_window) > self.controls["goettingen_win_size"]:
            self.goettingen_window.pop(0)

    def _try_join(self, berlin_tuple, goettingen_tuple):
        """
        Join two records when their timestamp difference is
        within the selected fuzzy tolerance.
        """

        ts1, city1, pm10_1, pm25_1 = berlin_tuple
        ts2, city2, pm10_2, pm25_2 = goettingen_tuple

        time_difference = abs((ts1 - ts2).total_seconds()) / 60

        if time_difference > self.controls["tolerance_minutes"]:
            return

        # Avoid emitting the same pair twice.
        pair_key = (ts1, ts2)

        if pair_key in self.emitted_pairs:
            return

        self.emitted_pairs.add(pair_key)

        pm10_difference = abs(pm10_1 - pm10_2)

        output_tuple = (
            ts1,
            ts2,
            pm10_1,
            pm10_2,
            time_difference,
            pm10_difference,
            pm25_1,
            pm25_2,
            format_window(self.berlin_window),
            format_window(self.goettingen_window)
        )

        self.output_stream.put(output_tuple)

    def run(self):
        while True:
            # Read the next tuple from both streams.
            berlin_tuple = self.input_stream_1.get()
            goettingen_tuple = self.input_stream_2.get()

            if (
                berlin_tuple[0] == "END"
                or goettingen_tuple[0] == "END"
            ):
                self.output_stream.put(
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
                        None
                    )
                )
                break

            # Add the new tuples to their windows.
            self.berlin_window.append(berlin_tuple)
            self.goettingen_window.append(goettingen_tuple)

            # Remove old tuples according to the GUI settings.
            self._trim_windows()

            # Compare the new Berlin tuple with every Goettingen
            # tuple currently available in its window.
            for g_tuple in self.goettingen_window:
                self._try_join(berlin_tuple, g_tuple)

            # Compare the new Goettingen tuple with every Berlin
            # tuple currently available in its window.
            for b_tuple in self.berlin_window:
                self._try_join(b_tuple, goettingen_tuple)

            time.sleep(random.random() * 0.2)
class PrintSinkBolt:
    def __init__(self, input_stream, b_str, g_str, gui_instance, on_complete=None):
        self.input_stream = input_stream
        self.b_str = b_str
        self.g_str = g_str
        self.gui_instance = gui_instance
		# @@@ Called when this run finishes.
        self.on_complete = on_complete		
    def run(self):
        print("\nStorm-Style Fuzzy Join with Dynamic Sliding Pipeline Windows")
        print("-" * 220)

        # @@@ Updated terminal header: now it shows both Berlin and Goettingen windows.
        print(
            f"{'Berlin Time':<20} "
            f"{'Goettingen Time':<20} "
            f"{'Time Diff':<10} "
            f"{'Berlin PM10':<12} "
            f"{'Goettingen PM10':<16} "
            f"{'PM10 Diff':<10} "
            f"{'Berlin Window':<55} "
            f"{'Goettingen Window'}"
        )
        print("-" * 220)

        while True:
            tuple_data = self.input_stream.get()

            if len(tuple_data) == 10:
                ts1, ts2, pm10_1, pm10_2, time_diff, pm10_diff, pm25_1, pm25_2, b_win, g_win = tuple_data

                if ts1 == "END":
                    self.gui_instance.update_ui("END", None, 0, 0, 0, 0, "", "", 0, 0)
                    print("-" * 220)
                    print("End of stream.")

                    # @@@ Tell the main program that this run is finished.
                    if self.on_complete is not None:
                        self.on_complete()

                    break

                # @@@ Updated terminal print: now it prints both dynamic windows.
                print(
                    f"{str(ts1):<20} "
                    f"{str(ts2):<20} "
                    f"{time_diff:<10.2f} "
                    f"{pm10_1:<12.2f} "
                    f"{pm10_2:<16.2f} "
                    f"{pm10_diff:<10.2f} "
                    f"{b_win:<55} "
                    f"{g_win}"
                )

                # @@@ GUI receives both windows and stream buffer counts.
                self.gui_instance.update_ui(
                    ts1,
                    ts2,
                    pm10_1,
                    pm10_2,
                    time_diff,
                    pm10_diff,
                    b_win,
                    g_win,
                    self.b_str.get_cnt(),
                    self.g_str.get_cnt()
                )

            time.sleep(random.random() * 0.1)


# =================================================================================================
# 4. RUNTIME SYSTEM LIFECYCLE: TOPOLOGY
# =================================================================================================
if __name__ == '__main__':
    # @@@ Shared dynamic parameters controlled by the UI sliders.
    topology_parameters = {
        "berlin_win_size": 4,
        "goettingen_win_size": 4,
        "tolerance_minutes": 15
    }

    dash = AirQualityDash(topology_controls=topology_parameters)

    # @@@ This prevents starting a new run while another run is still active.
    run_state = {
        "running": False,
        "run_number": 0
    }

    def mark_run_finished():
        # @@@ Called by PrintSinkBolt when the stream reaches END.
        run_state["running"] = False
        dash.alarm_bar.configure(
            text="🏁 RUN FINISHED. CHANGE VALUES AND CLICK RUN AGAIN.",
            bg="#37474F"
        )

    def start_topology_run():
        # @@@ Make sure slider values are copied into topology_parameters.
        dash._push_controls()

        if run_state["running"]:
            dash.alarm_bar.configure(
                text="⚠️ A TOPOLOGY RUN IS ALREADY ACTIVE. WAIT UNTIL IT FINISHES.",
                bg="#F57C00"
            )
            return

        run_state["running"] = True
        run_state["run_number"] += 1

        current_run = run_state["run_number"]

        print("\n" + "=" * 100)
        print(f"STARTING TOPOLOGY RUN #{current_run}")
        print(
            f"Berlin Window Size = {topology_parameters['berlin_win_size']} | "
            f"Goettingen Window Size = {topology_parameters['goettingen_win_size']} | "
            f"Tolerance / Time Difference = {topology_parameters['tolerance_minutes']} minutes"
        )
        print("=" * 100)

        dash.alarm_bar.configure(
            text=(
                f"▶ RUN #{current_run} ACTIVE | "
                f"Berlin Window={topology_parameters['berlin_win_size']} | "
                f"Goettingen Window={topology_parameters['goettingen_win_size']} | "
                f"Tolerance={topology_parameters['tolerance_minutes']}m"
            ),
            bg="#0D47A1"
        )

        # @@@ IMPORTANT:
        # @@@ Create NEW streams for every run.
        # @@@ This resets the pipeline completely.
        berlin_stream = stream("Berlin Spout-to-Join Stream", 10)
        goettingen_stream = stream("Goettingen Spout-to-Join Stream", 10)
        joined_stream = stream("Join-to-Sink Stream", 10)

        # @@@ Berlin spout has no time shift.
        berlin_spout = PMDataSpout(
            output_stream=berlin_stream,
            selected_city="Berlin",
            lat=52.52,
            lon=13.41,
            max_rows=80,
            time_shift_minutes=0
        )

        # @@@ Goettingen uses the dynamic tolerance value as the artificial time difference.
        # @@@ Example: if tolerance slider = 20, Goettingen is shifted by 20 minutes.
        goettingen_spout = PMDataSpout(
            output_stream=goettingen_stream,
            selected_city="Goettingen",
            lat=51.54,
            lon=9.93,
            max_rows=80,
            time_shift_minutes=topology_parameters["tolerance_minutes"]
        )

        # @@@ FuzzyJoinBolt also receives the same dynamic values.
        fuzzy_join_bolt = FuzzyJoinBolt(
            input_stream_1=berlin_stream,
            input_stream_2=goettingen_stream,
            output_stream=joined_stream,
            shared_controls=topology_parameters
        )

        sink_bolt = PrintSinkBolt(
            input_stream=joined_stream,
            b_str=berlin_stream,
            g_str=goettingen_stream,
            gui_instance=dash,

            # @@@ This allows the program to know when the run ended.
            on_complete=mark_run_finished
        )

        # @@@ Start a fresh Storm-style topology run.
        threading.Thread(
            name=f"BerlinPMDataSpout-Run-{current_run}",
            target=berlin_spout.run,
            daemon=True
        ).start()

        threading.Thread(
            name=f"GoettingenPMDataSpout-Run-{current_run}",
            target=goettingen_spout.run,
            daemon=True
        ).start()

        threading.Thread(
            name=f"FuzzyJoinBolt-Run-{current_run}",
            target=fuzzy_join_bolt.run,
            daemon=True
        ).start()

        threading.Thread(
            name=f"PrintSinkBolt-Run-{current_run}",
            target=sink_bolt.run,
            daemon=True
        ).start()

    # @@@ Connect the Run button to the topology starter.
    dash.set_run_callback(start_topology_run)

    # @@@ Open UI only.
    # @@@ The stream does NOT start automatically anymore.
    dash.root.mainloop()
    # @@@ These values can change during runtime from the GUI sliders.
    topology_parameters = {
        "berlin_win_size": 4,
        "goettingen_win_size": 4,
        "tolerance_minutes": 15
    }

    dash = AirQualityDash(topology_controls=topology_parameters)

    berlin_stream = stream("Berlin Spout-to-Join Stream", 10)
    goettingen_stream = stream("Goettingen Spout-to-Join Stream", 10)
    joined_stream = stream("Join-to-Sink Stream", 10)

    berlin_spout = PMDataSpout(
        output_stream=berlin_stream,
        selected_city="Berlin",
        lat=52.52,
        lon=13.41,
        max_rows=80,
        time_shift_minutes=0
    )

    goettingen_spout = PMDataSpout(
		output_stream=goettingen_stream,
		selected_city="Goettingen",
		lat=51.54,
		lon=9.93,
		max_rows=80,

		# @@@ No fixed shift anymore.
		time_shift_minutes=0,

		# @@@ Pass the same dynamic GUI controls into the spout.
		shared_controls=topology_parameters,

		# @@@ Goettingen time shift now uses tolerance_minutes dynamically.
		use_dynamic_time_shift=True
	)

    fuzzy_join_bolt = FuzzyJoinBolt(
        input_stream_1=berlin_stream,
        input_stream_2=goettingen_stream,
        output_stream=joined_stream,

        # @@@ Pass shared dynamic controls into the bolt.
        shared_controls=topology_parameters
    )

    sink_bolt = PrintSinkBolt(
        input_stream=joined_stream,
        b_str=berlin_stream,
        g_str=goettingen_stream,
        gui_instance=dash
    )

    # @@@ Storm-style topology components run in parallel threads.
    threading.Thread(
        name="BerlinPMDataSpout",
        target=berlin_spout.run,
        daemon=True
    ).start()

    threading.Thread(
        name="GoettingenPMDataSpout",
        target=goettingen_spout.run,
        daemon=True
    ).start()

    threading.Thread(
        name="FuzzyJoinBolt",
        target=fuzzy_join_bolt.run,
        daemon=True
    ).start()

    threading.Thread(
        name="PrintSinkBolt",
        target=sink_bolt.run,
        daemon=True
    ).start()

    dash.root.mainloop()