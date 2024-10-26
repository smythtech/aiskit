#!/usr/bin/python3

import json, argparse, math

def encode_for_ais(text, length):
  ais_chars = '@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_ !"#$%&\'()*+,-./0123456789:;<=>?'
  text = text.upper().ljust(length)[:length]  # Pad or trim text to fit length
  encoded = ''.join(format(ais_chars.index(c), '06b') for c in text)
  return encoded

def build_bitstream(data):

  message_type = 5
  repeat_indicator = data.get("repeat_indicator", 0)
  mmsi = data["mmsi"]
  ais_version = data.get("ais_version", 0)
  imo_number = data.get("imo_number", 0)
  call_sign = data["call_sign"]
  vessel_name = data["vessel_name"]
  ship_type = data["ship_type"]
  dimension_to_bow = data["dimension_to_bow"]
  dimension_to_stern = data["dimension_to_stern"]
  dimension_to_port = data["dimension_to_port"]
  dimension_to_starboard = data["dimension_to_starboard"]
  position_fix_type = data["position_fix_type"]
  eta_month = data["eta_month"]
  eta_day = data["eta_day"]
  eta_hour = data["eta_hour"]
  eta_minute = data["eta_minute"]
  draught = int(data["draught"] * 10)
  destination = data["destination"]
  dte = data.get("dte", 0)

  bitstream = (
    format(message_type, '06b') +
    format(repeat_indicator, '02b') +
    format(mmsi, '030b') +
    format(ais_version, '02b') +
    format(imo_number, '030b') +
    encode_for_ais(call_sign, 7) +
    encode_for_ais(vessel_name, 20) +
    format(ship_type, '08b') +
    format(dimension_to_bow, '09b') +
    format(dimension_to_stern, '09b') +
    format(dimension_to_port, '06b') +
    format(dimension_to_starboard, '06b') +
    format(position_fix_type, '04b') +
    format(eta_month, '04b') +
    format(eta_day, '05b') +
    format(eta_hour, '05b') +
    format(eta_minute, '06b') +
    format(draught, '08b') +
    encode_for_ais(destination, 20) +
    format(dte, '01b') +
    '0' * 5
  )
  bitstream = bitstream.ljust(424, '0')

  return bitstream

def calculate_checksum(nmea_sentence):
  checksum = 0
  for char in nmea_sentence:
    checksum ^= ord(char)
  return format(checksum, '02X')

def to_sixbit_ascii(bitstream):
  """Convert a 6-bit bitstream into AIS six-bit ASCII characters."""
  result = []
  for i in range(0, len(bitstream), 6):
    sixbit_value = int(bitstream[i:i+6], 2)
    result.append(sixbit_to_ascii(sixbit_value))
  return ''.join(result)

def sixbit_to_ascii(value):
  """Convert a six-bit integer value into an AIS ASCII character."""
  if 0 <= value <= 39:
    return chr(value + 48)  # Maps to '0' through 'W'
  elif 40 <= value <= 63:
    return chr(value + 56)  # Maps to '`' through 'w'
  else:
    raise ValueError("Invalid 6-bit value for AIS character decoding")

def build_nmea(bitstream):
  channel = "A"
  payload = to_sixbit_ascii(bitstream)
  nmea_sentences = []
  max_payload_length = 62
  total_fragments = math.ceil(len(payload) / max_payload_length)
  seq_num = ""
  if(total_fragments > 1):
    seq_num = "9"

  for fragment_number in range(total_fragments):
    fragment_payload = payload[fragment_number * max_payload_length:(fragment_number + 1) * max_payload_length]
    sentence = f"!AIVDM,{total_fragments},{fragment_number + 1},{seq_num},{channel},{fragment_payload},0"
    checksum = calculate_checksum(sentence[1:])
    nmea_sentence = f"{sentence}*{checksum}"
    nmea_sentences.append(nmea_sentence)

  return nmea_sentences

def handle_args():
  parser = argparse.ArgumentParser(prog="aiscraft.py", description="Build custom AIS type 5 message.", epilog="Author: Dylan Smyth (https://github.com/smythtech)")
  parser.add_argument("-r", "--read", help="NMEA AIS message contents JSON file.", required=True)
  parser.add_argument('--version', action='version', version='%(prog)s 1.0')

  return parser.parse_args()

def main():

  args = handle_args()
  json_data = {}

  with open(args.read, 'r') as f:
    json_data = json.loads(f.read())

  bitstream = build_bitstream(json_data)
  nmea = build_nmea(bitstream)

  for msg in nmea:
    print(msg)

if __name__ == '__main__':
  main()
