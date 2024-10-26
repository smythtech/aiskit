#!/usr/bin/python3

import signal, argparse

def decode_armored_ascii(ais_message):
  bitstream = ""
  for char in ais_message:
    sixbit_value = ascii_to_sixbit(char)
    bitstream += format(sixbit_value, '06b')
  return bitstream

def ascii_to_sixbit(char):
  value = ord(char)
  if 48 <= value <= 87:  # '0' (48) -> 0 to 'W' (87) -> 39
    return value - 48
  elif 96 <= value <= 119:  # '`' (96) -> 40 to 'w' (119) -> 63
    return value - 56
  else:
    raise ValueError("Invalid AIS character")

def sixbit_to_ascii(bitstream, start, length):
  AIS_CHARACTERS = "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_ !\"#$%&'()*+,-./0123456789:;<=>?"
  text = ""
  for i in range(start, start + length, 6):
    char_val = int(bitstream[i:i + 6], 2)
    if char_val < len(AIS_CHARACTERS):
     text += AIS_CHARACTERS[char_val]
    else:
     text += " "
  return text.strip().rstrip('@')

def parse_binary_data_payload(payload):
  text = ""
  for i in range(0, len(payload), 6):
    char_code = int(payload[i:i+6], 2) + 48
    text += chr(char_code) if char_code < 128 else '?'
  return text

def parse_default(bitstream):
  message_type = int(bitstream[0:6], 2)
  data = int(bitstream[6:], 2)

  return {
    "Message Type": message_type,
    "Data": data
  }

def parse_position_report(bitstream):
  # Interpret the bitstream according to AIS Message Type 1 structure
  message_type = int(bitstream[0:6], 2)          # Bits 0-5: Message Type
  repeat_indicator = int(bitstream[6:8], 2)      # Bits 6-7: Repeat Indicator
  mmsi = int(bitstream[8:38], 2)                 # Bits 8-37: MMSI
  navigation_status = int(bitstream[38:42], 2)   # Bits 38-41: Navigation Status
  speed = int(bitstream[50:60], 2) / 10.0        # Bits 50-59: Speed over ground (in knots)
  position_accuracy = int(bitstream[60:61], 2)   # Bit 60: Position Accuracy
  longitude = int(bitstream[61:89], 2) / 600000.0 # Bits 61-88: Longitude (in degrees)
  latitude = int(bitstream[89:116], 2) / 600000.0 # Bits 89-115: Latitude (in degrees)
  course = int(bitstream[116:128], 2) / 10.0      # Bits 116-127: Course over ground (in degrees)
  heading = int(bitstream[128:137], 2)           # Bits 128-136: True Heading (in degrees)

  return {
      "Message Type": message_type,
      "Repeat Indicator": repeat_indicator,
      "MMSI": mmsi,
      "Navigation Status": navigation_status,
      "Speed (knots)": speed,
      "Position Accuracy": position_accuracy,
      "Longitude": longitude,
      "Latitude": latitude,
      "Course (degrees)": course,
      "Heading (degrees)": heading,
  }

def parse_static_voyage_report(bitstream):
  # Interpret the bitstream according to AIS Message Type 5 structure
  message_type = int(bitstream[0:6], 2)                # Bits 0-5: Message Type
  repeat_indicator = int(bitstream[6:8], 2)            # Bits 6-7: Repeat Indicator
  mmsi = int(bitstream[8:38], 2)                       # Bits 8-37: MMSI
  ais_version = int(bitstream[38:40], 2)               # Bits 38-39: AIS Version
  imo_number = int(bitstream[40:70], 2)                # Bits 40-69: IMO Number
  call_sign = sixbit_to_ascii(bitstream, 70, 42)       # Bits 70-111: Call Sign (7 characters, 6 bits each)
  vessel_name = sixbit_to_ascii(bitstream, 112, 120)   # Bits 112-231: Vessel Name (20 characters, 6 bits each)
  ship_type = int(bitstream[232:240], 2)               # Bits 232-239: Ship Type
  to_bow = int(bitstream[240:249], 2)                  # Bits 240-248: Bow Dimension
  to_stern = int(bitstream[249:258], 2)                # Bits 249-257: Stern Dimension
  to_port = int(bitstream[258:264], 2)                 # Bits 258-263: Port Dimension
  to_starboard = int(bitstream[264:270], 2)            # Bits 264-269: Starboard Dimension
  vessel_length = to_bow + to_stern
  vessel_beam = to_port + to_starboard
  position_fixing_device_type = int(bitstream[270:274], 2)  # Bits 270-273: Position Fixing Device Type
  eta_month = int(bitstream[274:278], 2)
  eta_day = int(bitstream[278:283], 2)
  eta_hour = int(bitstream[283:288], 2)
  eta_minute = int(bitstream[288:294], 2)
  draught = int(bitstream[294:302], 2) / 10.0
  destination = sixbit_to_ascii(bitstream, 302, 120)

  return {
      "Message Type": message_type,
      "Repeat Indicator": repeat_indicator,
      "MMSI": mmsi,
      "AIS Version": ais_version,
      "IMO Number": imo_number,
      "Call Sign": call_sign,
      "Vessel Name": vessel_name,
      "Ship Type": ship_type,
      "Dimensions (Bow, Stern, Port, Starboard)": (to_bow, to_stern, to_port, to_starboard),
      "Vessel Length (meters)": vessel_length,
      "Vessel Beam (meters)": vessel_beam,
      "Position Fixing Device Type": position_fixing_device_type,
      "ETA (MM-DD HH:MM)": f"{eta_month:02}-{eta_day:02} {eta_hour:02}:{eta_minute:02}",
      "Maximum Draught (meters)": draught,
      "Destination": destination,
  }

def parse_base_station_report(bitstream):
  # Interpret the bitstream according to AIS Message Type 4 structure
  message_type = int(bitstream[0:6], 2)
  repeat_indicator = int(bitstream[6:8], 2)
  mmsi = int(bitstream[8:38], 2)
  utc_year = int(bitstream[38:52], 2)  # UTC Year (14 bits)
  utc_month = int(bitstream[52:56], 2)  # UTC Month (4 bits)
  utc_day = int(bitstream[56:61], 2)  # UTC Day (5 bits)
  utc_hour = int(bitstream[61:66], 2)  # UTC Hour (5 bits)
  utc_minute = int(bitstream[66:72], 2)  # UTC Minute (6 bits)
  utc_second = int(bitstream[72:78], 2)  # UTC Second (6 bits)
  position_accuracy = int(bitstream[78:79], 2)  # Position Accuracy (1 bit)
  longitude = int(bitstream[79:107], 2) / 600000.0  # Longitude (28 bits, scaled by 1/600000)
  if longitude >= 180:
    longitude -= 360  # Adjust for signed value
  latitude = int(bitstream[107:134], 2) / 600000.0  # Latitude (27 bits, scaled by 1/600000)
  if latitude >= 90:
    latitude -= 180  # Adjust for signed value
  fix_type = int(bitstream[134:138], 2) # Fix Type (4 bits)
  raim_flag = int(bitstream[148:149], 2) # RAIM flag (1 bit)
  reserved = int(bitstream[149:150], 2)

  return {
        "Message Type": message_type,
        "Repeat Indicator": repeat_indicator,
        "MMSI": mmsi,
        "UTC Year": utc_year,
        "UTC Month": utc_month,
        "UTC Day": utc_day,
        "UTC Hour": utc_hour,
        "UTC Minute": utc_minute,
        "UTC Second": utc_second,
        "Position Accuracy": "High" if position_accuracy == 1 else "Low",
        "Longitude": longitude,
        "Latitude": latitude,
        "Fix Type": fix_type,
        "RAIM Flag": "In Use" if raim_flag == 1 else "Not In Use",
        "Reserved": reserved,
  }

def parse_addressed(bitstream):
  # Interpret bitstream according to AIS Message Type 6 structure
  message_type = int(bitstream[0:6], 2)
  repeat_indicator = int(bitstream[6:8], 2)
  mmsi_sender = int(bitstream[8:38], 2)
  sequence_number = int(bitstream[38:40], 2)
  mmsi_destination = int(bitstream[40:70], 2)
  retransmit_flag = int(bitstream[70:71], 2)
  spare = int(bitstream[71:72], 2)
  application_identifier = int(bitstream[72:88], 2)
  binary_data_payload = str(bitstream[88:])
  binary_data_payload_text = parse_binary_data_payload(binary_data_payload)
  return {
      "Message Type": message_type,
      "Repeat Indicator": repeat_indicator,
      "MMSI Sender": mmsi_sender,
      "Sequence Number": sequence_number,
      "MMSI Destination": mmsi_destination,
      "Retransmit Flag": retransmit_flag,
      "Spare": spare,
      "Application Identifier": application_identifier,
      "Binary Data Payload": binary_data_payload,
      "Binary Data Payload (Decode attempt)": binary_data_payload_text
    }

def parse_broadcast(bitstream):
  # Interpret bitstream according to AIS Message Type 8 structure
  message_type = int(bitstream[0:6], 2)
  repeat_indicator = int(bitstream[6:8], 2)
  mmsi = int(bitstream[8:38], 2)
  spare = int(bitstream[38:40], 2)
  application_identifier = int(bitstream[40:56], 2)
  binary_data_payload = bitstream[56:]
  binary_data_payload_text = parse_binary_data_payload(binary_data_payload)

  return {
      "Message Type": message_type,
      "Repeat Indicator": repeat_indicator,
      "MMSI": mmsi,
      "Spare": spare,
      "Application Identifier": application_identifier,
      "Binary Data Payload": binary_data_payload_text
  }

def parse_sar_aircraft(bitstream):
  # Interpret bitstream according to AIS Message Type 9 structure
  message_type = int(bitstream[0:6], 2)
  repeat_indicator = int(bitstream[6:8], 2)
  mmsi = int(bitstream[8:38], 2)
  altitude = int(bitstream[38:50], 2)
  altitude = altitude if altitude < 4095 else None  # 4095 means "not available"
  sog = int(bitstream[50:60], 2)
  sog = sog if sog < 1023 else None  # 1023 means "not available"
  position_accuracy = int(bitstream[60:61], 2)
  raw_longitude = int(bitstream[61:89], 2)
  if raw_longitude >= (1 << 27):  # Convert two's complement for negative values
    raw_longitude -= (1 << 28)
  longitude = raw_longitude / 600000.0  # Scale to degrees
  raw_latitude = int(bitstream[89:116], 2)
  if raw_latitude >= (1 << 26):  # Convert two's complement for negative values
    raw_latitude -= (1 << 27)
  latitude = raw_latitude / 600000.0  # Scale to degrees
  cog = int(bitstream[116:128], 2)
  cog = cog / 10.0 if cog < 3600 else None  # Scale to degrees

  timestamp = int(bitstream[128:134], 2)
  dte = int(bitstream[134:135], 2)
  spare = int(bitstream[135:138], 2)

  return {
    "Message Type": message_type,
    "Repeat Indicator": repeat_indicator,
    "MMSI": mmsi,
    "Altitude": altitude if altitude is not None else "Not Available",
    "Speed Over Ground (knots)": sog if sog is not None else "Not Available",
    "Position Accuracy": "High" if position_accuracy == 1 else "Low",
    "Longitude": longitude,
    "Latitude": latitude,
    "Course Over Ground (degrees)": cog if cog is not None else "Not Available",
    "Time Stamp": timestamp,
    "DTE": "Available" if dte == 0 else "Not Available",
    "Spare": spare
  }

def parse_utc_req(bitstream):
  # Parse AIS Message Type 10 (UTC and Date Inquiry)
  message_type = int(bitstream[0:6], 2)
  repeat_indicator = int(bitstream[6:8], 2)
  mmsi = int(bitstream[8:38], 2)
  spare = int(bitstream[38:40], 2)
  destination_mmsi = int(bitstream[40:70], 2)
  spare_2 = int(bitstream[70:72], 2)

  return {
    "Message Type": message_type,
    "Repeat Indicator": repeat_indicator,
    "MMSI": mmsi,
    "Spare": spare,
    "Destination MMSI": destination_mmsi,
    "Spare 2": spare_2
  }


def parse_utc_resp(bitstream):
  # Parse AIS Message Type 11 (UTC and Date Response)
  message_type = int(bitstream[0:6], 2)
  repeat_indicator = int(bitstream[6:8], 2)
  mmsi = int(bitstream[8:38], 2)
  utc_year = int(bitstream[38:52], 2)
  utc_month = int(bitstream[52:56], 2)
  utc_day = int(bitstream[56:61], 2)
  utc_hour = int(bitstream[61:66], 2)
  utc_minute = int(bitstream[66:72], 2)
  utc_second = int(bitstream[72:78], 2)
  position_accuracy = int(bitstream[78:79], 2)
  raw_longitude = int(bitstream[79:107], 2)
  if raw_longitude >= (1 << 27):  # Convert two's complement for negative values
    raw_longitude -= (1 << 28)
  longitude = raw_longitude / 600000.0
  raw_latitude = int(bitstream[107:134], 2)
  if raw_latitude >= (1 << 26):  # Convert two's complement for negative values
    raw_latitude -= (1 << 27)
  latitude = raw_latitude / 600000.0
  position_fix_type = int(bitstream[134:138], 2)
  spare = int(bitstream[138:148], 2)
  raim_flag = int(bitstream[148:149], 2)
  communication_state = int(bitstream[149:168], 2)

  return {
    "Message Type": message_type,
    "Repeat Indicator": repeat_indicator,
    "MMSI": mmsi,
    "UTC Year": utc_year,
    "UTC Month": utc_month,
    "UTC Day": utc_day,
    "UTC Hour": utc_hour,
    "UTC Minute": utc_minute,
    "UTC Second": utc_second,
    "Position Accuracy": "High" if position_accuracy == 1 else "Low",
    "Longitude": longitude,
    "Latitude": latitude,
    "Position Fix Type": position_fix_type,
    "Spare": spare,
    "RAIM Flag": raim_flag,
    "Communication State": communication_state
  }

def parse_assignment(bitstream):
  # Parse AIS Message Type 16 (Assignment Mode Command)
  message_type = int(bitstream[0:6], 2)
  repeat_indicator = int(bitstream[6:8], 2)
  mmsi = int(bitstream[8:38], 2)
  spare_1 = int(bitstream[38:40], 2)
  destination_mmsi_1 = int(bitstream[40:70], 2)
  offset_1 = int(bitstream[70:82], 2)
  increment_1 = int(bitstream[82:92], 2)
  spare_2 = int(bitstream[92:94], 2)
  if len(bitstream) > 94:
    destination_mmsi_2 = int(bitstream[94:124], 2)
    offset_2 = int(bitstream[124:136], 2)
    increment_2 = int(bitstream[136:146], 2)
    spare_3 = int(bitstream[146:148], 2)
  else:
    destination_mmsi_2 = None
    offset_2 = None
    increment_2 = None
    spare_3 = None

  return {
    "Message Type": message_type,
    "Repeat Indicator": repeat_indicator,
    "MMSI": mmsi,
    "Spare 1": spare_1,
    "Destination MMSI 1": destination_mmsi_1,
    "Offset 1": offset_1,
    "Increment 1": increment_1,
    "Spare 2": spare_2,
    "Destination MMSI 2": destination_mmsi_2,
    "Offset 2": offset_2,
    "Increment 2": increment_2,
    "Spare 3": spare_3
  }

def parse_dgnss_broadcast(bitstream):
  # Parse AIS Message Type 17 (GNSS Broadcast Binary Message)
  message_type = int(bitstream[0:6], 2)
  repeat_indicator = int(bitstream[6:8], 2)
  mmsi = int(bitstream[8:38], 2)
  spare_1 = int(bitstream[38:40], 2)
  raw_longitude = int(bitstream[40:58], 2)
  if raw_longitude >= (1 << 17):  # Convert two's complement for negative values
    raw_longitude -= (1 << 18)
  longitude = raw_longitude / 600000.0
  raw_latitude = int(bitstream[58:75], 2)
  if raw_latitude >= (1 << 16):  # Convert two's complement for negative values
    raw_latitude -= (1 << 17)
  latitude = raw_latitude / 600000.0
  spare_2 = int(bitstream[75:80], 2)
  binary_data = bitstream[80:]

  return {
    "Message Type": message_type,
    "Repeat Indicator": repeat_indicator,
    "MMSI": mmsi,
    "Spare 1": spare_1,
    "Longitude": longitude,
    "Latitude": latitude,
    "Spare 2": spare_2,
    "Binary Data": binary_data
  }

def parse_class_b_pos_report(bitstream):
  # Parse AIS Message Type 18 (Standard Class B Equipment Position Report)
  message_type = int(bitstream[0:6], 2)
  repeat_indicator = int(bitstream[6:8], 2)
  mmsi = int(bitstream[8:38], 2)
  reserved = int(bitstream[38:46], 2)
  sog = int(bitstream[46:56], 2)
  sog = sog / 10.0 if sog < 1023 else None  # 1023 means "not available"
  position_accuracy = int(bitstream[56:57], 2)
  raw_longitude = int(bitstream[57:85], 2)
  if raw_longitude >= (1 << 27):  # Convert two's complement for negative values
    raw_longitude -= (1 << 28)
  longitude = raw_longitude / 600000.0
  raw_latitude = int(bitstream[85:112], 2)
  if raw_latitude >= (1 << 26):  # Convert two's complement for negative values
    raw_latitude -= (1 << 27)
  latitude = raw_latitude / 600000.0
  cog = int(bitstream[112:124], 2) / 10.0  # Course Over Ground, scaled to degrees
  true_heading = int(bitstream[124:133], 2)
  timestamp = int(bitstream[133:139], 2)
  cs_unit_flag = int(bitstream[139:140], 2)
  display_flag = int(bitstream[140:141], 2)
  dsc_flag = int(bitstream[141:142], 2)
  band_flag = int(bitstream[142:143], 2)
  msg_22_flag = int(bitstream[143:144], 2)
  mode_flag = int(bitstream[144:145], 2)
  raim_flag = int(bitstream[145:146], 2)
  radio_status = int(bitstream[146:166], 2)

  return {
    "Message Type": message_type,
    "Repeat Indicator": repeat_indicator,
    "MMSI": mmsi,
    "Reserved": reserved,
    "Speed Over Ground (knots)": sog if sog is not None else "Not Available",
    "Position Accuracy": "High" if position_accuracy == 1 else "Low",
    "Longitude": longitude,
    "Latitude": latitude,
    "Course Over Ground (degrees)": cog,
    "True Heading": true_heading if true_heading < 360 else "Not Available",
    "Timestamp": timestamp,
    "CS Unit Flag": cs_unit_flag,
    "Display Flag": display_flag,
    "DSC Flag": dsc_flag,
    "Band Flag": band_flag,
    "Message 22 Flag": msg_22_flag,
    "Mode Flag": mode_flag,
    "RAIM Flag": raim_flag,
    "Radio Status": radio_status
  }

def parse_class_b_ext_pos_report(bitstream):
  message_type = int(bitstream[0:6], 2)
  repeat_indicator = int(bitstream[6:8], 2)
  mmsi = int(bitstream[8:38], 2)
  sog = int(bitstream[46:56], 2) / 10.0  # Speed Over Ground
  position_accuracy = int(bitstream[56:57], 2)
  raw_longitude = int(bitstream[57:85], 2)
  if raw_longitude >= (1 << 27):
    raw_longitude -= (1 << 28)
  longitude = raw_longitude / 600000.0
  raw_latitude = int(bitstream[85:112], 2)
  if raw_latitude >= (1 << 26):
    raw_latitude -= (1 << 27)
  latitude = raw_latitude / 600000.0
  cog = int(bitstream[112:124], 2) / 10.0
  true_heading = int(bitstream[124:133], 2)
  timestamp = int(bitstream[133:139], 2)
  vessel_name = sixbit_to_ascii(bitstream, 143, 120)  # Vessel Name
  ship_type = int(bitstream[263:271], 2)
  dimension_to_bow = int(bitstream[271:280], 2)
  dimension_to_stern = int(bitstream[280:289], 2)
  dimension_to_port = int(bitstream[289:295], 2)
  dimension_to_starboard = int(bitstream[295:301], 2)

  return {
    "Message Type": message_type,
    "MMSI": mmsi,
    "Speed Over Ground (knots)": sog,
    "Position Accuracy": position_accuracy,
    "Longitude": longitude,
    "Latitude": latitude,
    "Course Over Ground (degrees)": cog,
    "True Heading": true_heading,
    "Timestamp": timestamp,
    "Vessel Name": vessel_name,
    "Ship Type": ship_type,
    "Dimensions": {
      "To Bow": dimension_to_bow,
      "To Stern": dimension_to_stern,
      "To Port": dimension_to_port,
      "To Starboard": dimension_to_starboard
    }
  }

def parse_dl_mgmt(bitstream):
  message_type = int(bitstream[0:6], 2)
  mmsi = int(bitstream[8:38], 2)
  offset_1 = int(bitstream[40:52], 2)
  num_slots_1 = int(bitstream[52:56], 2)
  timeout_1 = int(bitstream[56:59], 2)
  increment_1 = int(bitstream[59:69], 2)
  offset_2 = int(bitstream[69:81], 2) if len(bitstream) > 81 else None

  return {
    "Message Type": message_type,
    "MMSI": mmsi,
    "Offsets": [offset_1, offset_2],
    "Num Slots": num_slots_1,
    "Timeout": timeout_1,
    "Increment": increment_1
  }

def parse_aids_to_nav_report(bitstream):
  message_type = int(bitstream[0:6], 2)
  mmsi = int(bitstream[8:38], 2)
  aid_type = int(bitstream[38:43], 2)
  name = sixbit_to_ascii(bitstream, 43, 120)
  raw_longitude = int(bitstream[163:191], 2)
  if raw_longitude >= (1 << 27):
    raw_longitude -= (1 << 28)
  longitude = raw_longitude / 600000.0
  raw_latitude = int(bitstream[191:218], 2)
  if raw_latitude >= (1 << 26):
    raw_latitude -= (1 << 27)
  latitude = raw_latitude / 600000.0

  return {
    "Message Type": message_type,
    "MMSI": mmsi,
    "Aid Type": aid_type,
    "Name": name,
    "Longitude": longitude,
    "Latitude": latitude
  }

def parse_channel_mgmt(bitstream):
  message_type = int(bitstream[0:6], 2)
  mmsi = int(bitstream[8:38], 2)
  channel_a = int(bitstream[40:52], 2)
  channel_b = int(bitstream[52:64], 2)

  return {
    "Message Type": message_type,
    "MMSI": mmsi,
    "Channel A": channel_a,
    "Channel B": channel_b
  }

def parse_static_report(bitstream):
  message_type = int(bitstream[0:6], 2)
  mmsi = int(bitstream[8:38], 2)
  part_number = int(bitstream[38:40], 2)
  name = sixbit_to_ascii(bitstream, 40, 120) if part_number == 0 else None

  return {
    "Message Type": message_type,
    "MMSI": mmsi,
    "Part Number": part_number,
    "Name": name if name else "Not Available"
  }

def parse_single_slot_binary(bitstream):
  message_type = int(bitstream[0:6], 2)
  mmsi = int(bitstream[8:38], 2)
  address_flag = int(bitstream[38:39], 2)
  binary_data = bitstream[40:]

  return {
    "Message Type": message_type,
    "MMSI": mmsi,
    "Addressed Flag": address_flag,
    "Binary Data": binary_data
  }

def parse_ais(bitstream):
  return {
    1 : parse_position_report,
    2 : parse_position_report,
    3 : parse_position_report,
    4 : parse_base_station_report,
    5 : parse_static_voyage_report,
    6 : parse_addressed,
    8 : parse_broadcast,
    9 : parse_sar_aircraft,
    10: parse_utc_req,
    11: parse_utc_resp,
    16 : parse_assignment,
    17 : parse_dgnss_broadcast,
    18 : parse_class_b_pos_report,
    19 : parse_class_b_ext_pos_report,
    20 : parse_dl_mgmt,
    21 : parse_aids_to_nav_report,
    22 : parse_channel_mgmt,
    24 : parse_static_report,
    25 : parse_single_slot_binary
  }.get(int(bitstream[0:6], 2), parse_default)(bitstream)

def print_data(id_only, msg_dict):
  id_fields = ["MMSI", "Call Sign", "Vessel Name", "Name"]
  for key, value in msg_dict.items():
    if(id_only and key in id_fields):
      print(f"{key}: {value}")
    elif(not id_only):
      print(f"{key}: {value}")
  print()

def sig_handler(sig, frame):
  exit()

def handle_args():
  parser = argparse.ArgumentParser(prog="aisdump.py", description="Dump data from NMEA AIS messages.", epilog="Author: Dylan Smyth (https://github.com/smythtech)")
  parser.add_argument("-r", "--read", help="Input filename.", required=True)
  parser.add_argument("-t", "--type", help="Filter by message type.", required=False)
  parser.add_argument("-i", "--id-only", help="Dump ID data only (MMSIs, Names, Call Signs).", required=False, action='store_true')
  parser.add_argument('--version', action='version', version='%(prog)s 1.0')

  return parser.parse_args()

def main():

  signal.signal(signal.SIGINT, sig_handler)
  args = handle_args()

  frag_buffer = {}

  with open(args.read, 'r') as f:
    for msg in f:
      nmea_msg = msg.split(",")
      frags = int(nmea_msg[1])
      frag_num = int(nmea_msg[2])
      if(len(nmea_msg[3]) > 0):
        frag_seq = int(nmea_msg[3])
      ais_payload = nmea_msg[5]
      if(frags > 1):
        if(frag_seq in frag_buffer):
          frag_buffer[frag_seq] += ais_payload
          if(frags != frag_num):
             continue
          else:
            ais_payload = frag_buffer[frag_seq]
            frag_buffer.pop(frag_seq)
        else:
          frag_buffer[frag_seq] = ais_payload
          continue
      try:
        bitstream = decode_armored_ascii(ais_payload)
        if((args.type == None) or ((args.type != None) and (int(args.type) == int(bitstream[0:6], 2)))):
          msg_dict = parse_ais(bitstream)
          print_data(args.id_only, msg_dict)
      except TypeError as e:
        print(f"Error: {e}")
        exit()
      except Exception as e:
        print(f"Encountered error parsing message {nmea_msg}: {e}")

if __name__ == '__main__':
  main()

