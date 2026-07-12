import threading
import time
import random
import logging
import requests
import calendar
from datetime import datetime, timedelta


# simple stream with window size
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
			logging.debug("stream before blocking on full = %s" % str(self))
			self._mutex.wait()

		self._enqueue(t)
		self._mutex.notify()
		self._mutex.release()

	def get(self):
		self._mutex.acquire()

		while self._isempty():
			logging.debug("get blocked by empty stream")
			self._mutex.wait()

		t = self._dequeue()
		self._mutex.notify()
		self._mutex.release()

		return t

	def inspect(self):
		self._mutex.acquire()

		if self._isempty():
			logging.debug("inspect empty stream")
			t = None
		else:
			t = self._stream[self._rpos]

		self._mutex.release()
		return t


###################################################################################################
# Storm-style component 1:
# SPOUT
#
# A spout is a data source.
# Here, each PMDataSpout downloads data for one city and emits tuples into its output stream.
###################################################################################################

class PMDataSpout:
	def __init__(self, output_stream, selected_city, lat, lon, max_rows=80, time_shift_minutes=0):
		self.output_stream = output_stream
		self.selected_city = selected_city
		self.lat = lat
		self.lon = lon
		self.max_rows = max_rows
		self.time_shift_minutes = time_shift_minutes

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

						# Convert API timestamp to datetime object
						ts = datetime.fromisoformat(timestamp)

						# Artificial delay to make fuzzy join visible
						ts = ts + timedelta(minutes=self.time_shift_minutes)

						# Tuple format:
						# timestamp, city, pm10, pm2_5
						tuple_data = (ts, self.selected_city, pm10, pm25)

						# Storm-style emit
						self.output_stream.put(tuple_data)

						emitted_rows += 1

						if self.max_rows is not None and emitted_rows >= self.max_rows:
							self.output_stream.put(("END", self.selected_city, None, None))
							return

						time.sleep(0.05)

				except Exception as e:
					print(f"Error while loading API data for {self.selected_city}:", e)

		self.output_stream.put(("END", self.selected_city, None, None))


###################################################################################################
# Helper function:
# Shows the recent pipeline window in the terminal.
#
# Example:
# [00:00:6.3, 01:00:6.8, 02:00:6.8, 03:00:8.3]
###################################################################################################

def format_window(window):
	return "[" + ", ".join(
		f"{item[0].strftime('%H:%M')}:{item[2]:.1f}"
		for item in window
	) + "]"


###################################################################################################
# Storm-style component 2:
# BOLT
#
# This bolt receives two input streams:
# 1. Berlin stream
# 2. Goettingen stream
#
# It keeps a sliding pipeline window for both streams.
# It joins two tuples if their timestamps are within the tolerance.
###################################################################################################

class FuzzyJoinBolt:
	def __init__(self, input_stream_1, input_stream_2, output_stream, tolerance_minutes=60, window_size=4):
		self.input_stream_1 = input_stream_1
		self.input_stream_2 = input_stream_2
		self.output_stream = output_stream
		self.tolerance_minutes = tolerance_minutes
		self.window_size = window_size

		# Physical sliding windows for showing recent tuples in the pipeline
		self.berlin_window = []
		self.goettingen_window = []

	def run(self):
		t1 = self.input_stream_1.get()
		t2 = self.input_stream_2.get()

		while True:
			if t1[0] == "END" or t2[0] == "END":
				self.output_stream.put(("END", None, None, None, None, None, None, None, None, None))
				break

			# Berlin tuple
			ts1, city1, pm10_1, pm25_1 = t1

			# Goettingen tuple
			ts2, city2, pm10_2, pm25_2 = t2

			# New data enters the pipeline window
			self.berlin_window.append(t1)
			self.goettingen_window.append(t2)

			# Old data gets popped out when the window is full
			if len(self.berlin_window) > self.window_size:
				self.berlin_window.pop(0)

			if len(self.goettingen_window) > self.window_size:
				self.goettingen_window.pop(0)

			# Calculate time difference in minutes
			time_difference = abs((ts1 - ts2).total_seconds()) / 60

			# Fuzzy join condition
			if time_difference <= self.tolerance_minutes:
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

				# Storm-style emit
				self.output_stream.put(output_tuple)

				# Move forward in both streams after successful join
				t1 = self.input_stream_1.get()
				t2 = self.input_stream_2.get()

			else:
				# Move the earlier stream forward
				if ts1 < ts2:
					t1 = self.input_stream_1.get()
				else:
					t2 = self.input_stream_2.get()

			time.sleep(random.random() * 0.2)


###################################################################################################
# Storm-style component 3:
# SINK BOLT
#
# This consumes the final fuzzy join result and prints it.
###################################################################################################

class PrintSinkBolt:
	def __init__(self, input_stream):
		self.input_stream = input_stream

	def run(self):
		print("\nStorm-Style Fuzzy Join with Sliding Pipeline Windows")
		print("-" * 190)
		print(
			f"{'Berlin Time':<20} "
			f"{'Goettingen Time':<20} "
			f"{'Time Diff':<10} "
			f"{'Berlin PM10':<12} "
			f"{'Goettingen PM10':<16} "
			f"{'PM10 Diff':<10} "
			f"{'Berlin Window':<48} "
			f"{'Goettingen Window'}"
		)
		print("-" * 190)

		while True:
			tuple_data = self.input_stream.get()

			if len(tuple_data) == 10:
				ts1, ts2, pm10_1, pm10_2, time_diff, pm10_diff, pm25_1, pm25_2, berlin_window, goettingen_window = tuple_data

				if ts1 == "END":
					print("-" * 190)
					print("End of stream.")
					break

				print(
					f"{str(ts1):<20} "
					f"{str(ts2):<20} "
					f"{time_diff:<10.2f} "
					f"{pm10_1:<12.2f} "
					f"{pm10_2:<16.2f} "
					f"{pm10_diff:<10.2f} "
					f"{berlin_window:<48} "
					f"{goettingen_window}"
				)

			time.sleep(random.random() * 0.2)


###################################################################################################
# TOPOLOGY
#
# In Storm, a topology connects spouts and bolts.
#
# Our simplified Storm-style topology:
#
# Berlin PMDataSpout      \
#                          → FuzzyJoinBolt → PrintSinkBolt
# Goettingen PMDataSpout  /
###################################################################################################

logging.basicConfig(level=logging.WARNING)

# Streams between components
berlin_stream = stream("Berlin Spout-to-Join Stream", 10)
goettingen_stream = stream("Goettingen Spout-to-Join Stream", 10)
joined_stream = stream("Join-to-Sink Stream", 10)

# Spout 1: Berlin stream, no artificial delay
berlin_spout = PMDataSpout(
	output_stream=berlin_stream,
	selected_city="Berlin",
	lat=52.52,
	lon=13.41,
	max_rows=80,
	time_shift_minutes=0
)

# Spout 2: Goettingen stream, shifted by 30 minutes
# This makes the fuzzy join visible in the terminal.
goettingen_spout = PMDataSpout(
	output_stream=goettingen_stream,
	selected_city="Goettingen",
	lat=51.54,
	lon=9.93,
	max_rows=80,
	time_shift_minutes=30
)

# Fuzzy join bolt
fuzzy_join_bolt = FuzzyJoinBolt(
	input_stream_1=berlin_stream,
	input_stream_2=goettingen_stream,
	output_stream=joined_stream,
	tolerance_minutes=60,
	window_size=4
)

# Sink bolt
sink_bolt = PrintSinkBolt(
	input_stream=joined_stream
)

# Create threads
berlin_spout_thread = threading.Thread(
	name="BerlinPMDataSpout",
	target=berlin_spout.run
)

goettingen_spout_thread = threading.Thread(
	name="GoettingenPMDataSpout",
	target=goettingen_spout.run
)

fuzzy_join_thread = threading.Thread(
	name="FuzzyJoinBolt",
	target=fuzzy_join_bolt.run
)

sink_thread = threading.Thread(
	name="PrintSinkBolt",
	target=sink_bolt.run
)

# Start topology
fuzzy_join_thread.start()
sink_thread.start()
berlin_spout_thread.start()
goettingen_spout_thread.start()

# Wait until all components finish
berlin_spout_thread.join()
goettingen_spout_thread.join()
fuzzy_join_thread.join()
sink_thread.join()