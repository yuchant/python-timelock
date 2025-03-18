#!/usr/bin/env python3
DESCRIPTION = """
Theory:
   Time-lock puzzles and timed-release Crypto (1996)
   by Ronald L. Rivest, Adi Shamir, and David A. Wagner

Modified by Yuji Tomita 2015.
"""
import datetime

from Crypto.Util import number
from Crypto import Random
from Crypto.Cipher import AES
import sys
import time
import argparse

# Init PyCrypto RNG
# placeholder variable for packed files
if not 'puzzle' in locals():
    puzzle = None

SECOND = 1
MINUTE = 60
HOUR = MINUTE * 60
DAY = HOUR * 24
MONTH = DAY * 31
YEAR = DAY * 365

MOD_BITS = 2048 # for time-lock puzzle N
AES_BITS = 192

def calibrate_speed():
    p = number.getPrime(MOD_BITS//2, Random.get_random_bytes)
    q = number.getPrime(MOD_BITS//2, Random.get_random_bytes)
    N = p*q
    bignum = number.getRandomNBitInteger(MOD_BITS)
    start = time.time()
    trials = 100
    for i in range(trials):
        bignum = pow(bignum, 2, N)
    return int(trials/(time.time() - start))

SPEED = calibrate_speed()
SAVE_INTERVAL = SPEED * 10 * MINUTE

def aes_pad(msg, block_size=16):
    """Pads the message to a multiple of the block size using PKCS7 padding."""
    if isinstance(msg, str):
        msg = msg.encode()  # Convert string to bytes if needed
    pad_len = block_size - (len(msg) % block_size)    
    return msg + bytes([pad_len] * pad_len)

def aes_encode(msg, key):
    return AES.new(number.long_to_bytes(key), AES.MODE_ECB).encrypt(aes_pad(msg))

def aes_decode(ciphertext, key):
    return AES.new(number.long_to_bytes(key), AES.MODE_ECB).decrypt(ciphertext).rstrip(b'\0').decode('utf-8')

# Routine adapted from Anti-Emulation-through-TimeLock-puzzles
def makepuzzle(t):

    # Generate 512-bit primes
    p = number.getPrime(MOD_BITS//2, Random.get_random_bytes)
    q = number.getPrime(MOD_BITS//2, Random.get_random_bytes)
    N = p*q
    totient = (p-1)*(q-1)

    key = number.getRandomNBitInteger(AES_BITS)
    a = number.getRandomNBitInteger(MOD_BITS) % N

    e = pow(2, t, totient)
    b = pow(a, e, N)

    cipher_key = (key + b) % N
    return (key, {'N': N, 'a': a, 'steps': t, 'cipher_key': cipher_key})

def eta(remaining, speed):
    seconds = remaining/speed
    if seconds < 100 * SECOND:
        return '%d seconds' % seconds
    elif seconds < 100 * MINUTE:
        return '%d minutes' % (seconds/MINUTE)
    elif seconds < 100 * HOUR:
        return '%d hours' % (seconds/HOUR)
    elif seconds < 60 * DAY:
        return '%d days' % (seconds/DAY)
    elif seconds < 20 * MONTH:
        return '%d months' % (seconds/MONTH)
    else:
        return '%d years' % (seconds/YEAR)

def putestimation(outputstream, puzzle):
    outputstream.write("# Estimated time to solve: %s\n" % eta(puzzle['steps'], SPEED))

def save_puzzle(p):
    state = str(p)
    filename = 'puzzle_%d-%d' % (p['cipher_key'] % 1000000000000, p['steps']//SAVE_INTERVAL)
    with open(filename, 'w') as f:
        f.write('# Run ./timelock FILENAME > OUTFILE to decode\n')
        putestimation(f, p)
        f.write('\n')
        f.write(state)
    print("saved state:", filename, file=sys.stderr)

def solve_puzzle(p):
    tmp, N, t = p['a'], p['N'], p['steps']
    start = time.time()
    i = 0
    while i < t:
        if (i+1) % SAVE_INTERVAL == 0:
            p2 = p.copy()
            p2['steps'] = t-i
            p2['a'] = tmp
            save_puzzle(p2)
        tmp = pow(tmp, 2, N)
        if i % 12345 == 1:
            speed = i/(time.time() - start)
            sys.stderr.write('\r%f squares/s, %d remaining, eta %s \r'
                % (speed, t-i, eta(t-i, speed)))
        i += 1
    print(file=sys.stderr)
    return (p['cipher_key'] - tmp) % N

def _unpack():
    solution = solve_puzzle(puzzle)
    print("solution =", solution, file=sys.stderr)
    if 'ciphertext' in puzzle:
        result = aes_decode(puzzle['ciphertext'], solution)
        print(result)
    with open('decoded.txt', 'a') as f:
        f.write(result + "\n")


def _usage():
    if puzzle:
        print("""*** This is a self-decoding file ***

If no parameter is given, the embedded puzzle will be decoded.
""")
    print("""Usage: ./timelock.py <PARAM>
    --h|help                    display this message
    --new [time]                create a sample puzzle with solution time 'time'
    --encrypt <file> [time]     encode a file using AES with a random key
    --pack <file> [time]        pack a self-decoding file using this script
    --benchmark                 print number of operations per second
    <saved state>               print puzzle solution to stdout
    """)
    exit(2)

def _new_key_time0(time):
    try:
        time = int(sys.argv[2]) * SECOND
    except:
        time = 30 * SECOND
    print("Creating test puzzle with difficulty time %d" % time)
    (key, puzzle) = makepuzzle(time*SPEED)
    print("key:", str(key)) # Recover the key
    save_puzzle(puzzle)

def _encrypt_file_time0(file, time, value=None):
    if value is not None:
        msg = value
    else:
        with open(file, 'rb') as f:
            msg = f.read()
    try:
        time = int(time)
    except:
        try:
            time = int(sys.argv[3]) * SECOND
        except:
            time = 30 * SECOND
    (key, puzzle) = makepuzzle(time*SPEED)
    puzzle['ciphertext'] = aes_encode(msg, key)
    save_puzzle(puzzle)

def _pack_file_time0(self, file, time, value=None, save_to_file=None):
    if save_to_file is not None:
        from io import StringIO
        stdout = sys.stdout
        sys.stdout = StringIO()
    if value is not None:
        msg = value
    else:
        with open(file, 'rb') as f:
            msg = f.read()

    try:
        time = int(time)
    except:
        try:
            time = int(sys.argv[3]) * SECOND
        except:
            time = 30 * SECOND
    (key, puzzle) = makepuzzle(time*SPEED)
    puzzle['ciphertext'] = aes_encode(msg, key)
    print("#!/usr/bin/env python3")
    for line in DESCRIPTION.split('\n'):
        print("#", line)
    print("# Run this program to recover the original message.")
    print("# (scroll down see the program that generated this file)")
    print("#")
    putestimation(sys.stdout, puzzle)
    print("#")
    print()
    print("puzzle =", puzzle)
    with open(self) as f:
        print(f.read())
    if save_to_file is not None:
        with open(save_to_file, 'w') as f:
            f.write(sys.stdout.getvalue())
            sys.stdout = stdout

def _decode_file(file):
    try:
        print("Decoding %s" % file)
        with open(file) as f:
            puzzle = eval(f.read())
    except Exception as e:
        print("Error parsing saved state.", e)
        exit(1)
    solution = solve_puzzle(puzzle)
    print("solution =", solution, file=sys.stderr)
    if 'ciphertext' in puzzle:
        print(aes_decode(puzzle['ciphertext'], solution))

class Main(object):
    def __init__(self, args):
        self.args = args
        print(args, file=sys.stderr)

    def execute(self):
        if self.args.benchmark:
            self.benchmark()
        elif self.args.pack:
            self.pack()
        elif self.args.seconds_until_date or self.args.until_date:
            self.seconds_until_date(self.args.seconds_until_date or self.args.until_date)
        elif self.args.encrypt:
            self.encrypt()
        elif self.args.decode:
            _decode_file(self.args.decode)
        else:
            print("Exiting")
            sys.exit(1)

    def exit(self, msg=''):
        print("Exit: %s" % msg, file=sys.stderr)
        sys.exit(1)

    def encrypt(self):
        """ Encrypt a file now.
        """
        _encrypt_file_time0(
            None,
            self.get_time_to_decode_seconds(),
            value=self.get_value_to_encode(),
        )


    def pack(self, seconds=None, save_to_file=None):
        """ Pack a self encoding file to stdout.
        """
        self_file = sys.argv[0]
        print("Packing... ", seconds, save_to_file, file=sys.stderr)
        _pack_file_time0(
            self_file,
            None,
            seconds or self.get_time_to_decode_seconds(),
            value=self.get_value_to_encode(),
            save_to_file=save_to_file,
        )

    def get_time_to_decode_seconds(self):
        """ Get the time the user wishes to take to decode this file.
        """
        seconds = self.get_unit() * self.args.time
        print("Calculated seconds to: %s" % seconds, file=sys.stderr)
        return seconds

    def convert_date_to_seconds(self, date_string):
        """ Process a date string to seconds.
        """
        pass

    def get_unit(self):
        UNIT_MAP = {
            'seconds': SECOND,
            'minutes': MINUTE,
            'hours': HOUR,
            'days': DAY,
            'years': YEAR,
            'date': self.convert_date_to_seconds,
        }
        unit = self.args.unit
        seconds_per_value = UNIT_MAP[unit]
        return seconds_per_value

    def seconds_until_date(self, arg):
        """ Calculate seconds until a date.
        Common Time Zones for USA.
            'US/Alaska',
            'US/Arizona',
            'US/Central',
            'US/Eastern',
            'US/Hawaii',
            'US/Mountain',
            'US/Pacific',
            'UTC',
        """
        print('Calculating time until a date %s' % arg, file=sys.stderr)
        try:
            from dateutil import parser
            import pytz
        except ImportError:
            self.exit("You need to install python-dateutil and pytz to use the date functionality")

        COMMON_TZINFOS = {
            'PDT': pytz.timezone('US/Pacific'),
            'PST': pytz.timezone('US/Pacific'),
            'EST': pytz.timezone('US/Eastern'),
            'EDT': pytz.timezone('US/Eastern'),
            'CST': pytz.timezone('US/Central'),
        }
        date_format = '%m-%d-%Y %H:%M %Z'

        server_utc = datetime.datetime.now(pytz.utc)
        print("Server Now UTC: ",  server_utc, file=sys.stderr)
        server_est = server_utc.astimezone(pytz.timezone('US/Eastern'))
        print("Server Now EST: ", server_est, file=sys.stderr)

        if len(arg) > 1:
            arg = ' '.join(arg)
        else:
            arg = arg[0]
        target_date = parser.parse(arg)
        if self.args.tz:
            try:
                tz = COMMON_TZINFOS[self.args.tz]
            except KeyError:
                tz = pytz.timezone(self.args.tz)
            target_date_tz = tz.localize(target_date)
            target_date_utc = target_date_tz.astimezone(pytz.utc)
        else:
            proceed = input("No TZ passed. Assuming EST.\nProceed?\ny/n: ")
            if proceed != 'y':
                self.exit("Exited")
            tz = pytz.timezone('US/Eastern')
            target_date_tz = tz.localize(target_date)
            target_date_utc = target_date_tz.astimezone(pytz.utc)
        target_date_string = target_date_tz.strftime('%A, %B %Y at %I%p %Z').strip()
        print("Target Date UTC: ", target_date_utc, file=sys.stderr)
        print("Target Date %s: " % tz, target_date_string, file=sys.stderr)

        delta = target_date_tz - server_utc
        seconds = delta.total_seconds()


        default_filename = ''.join((
            'TARGET__',
            target_date_string.replace(' ', '_').replace(',', ''),
            ('-%.0fHRS' % (seconds/HOUR)),
            '.py'
        ))
        print("""Time difference is {delta}.
Seconds: {seconds:.0f}
Minutes: {minutes:.0f}
Hours: {hours:.1f}
Days: {days:.2f}
Target Unlock Date: {target_date}
""".format(
                delta=delta,
                seconds=seconds,
                minutes=seconds/MINUTE,
                hours=seconds/HOUR,
                days=seconds/DAY,
                target_date=target_date_string
        ), file=sys.stderr)
        filename = input("Enter the output file name\nLeave blank to default name:\n%s\n" % default_filename)
        self.pack(seconds, save_to_file=filename or default_filename)

    def get_value_to_encode(self):
        if self.args.file:
            with open(self.args.file, 'rb') as f:
                return f.read()
        elif self.args.value:
            return self.args.value
        self.exit("No string or file provided to encode")

    def benchmark(self):
        print("%d %d-bit modular exponentiations per second" % (SPEED, MOD_BITS))


def main():
    if puzzle:
        print('this is a self decoding file - decoding.', file=sys.stderr)
        _unpack()
        return

    parser = argparse.ArgumentParser()
    parser.add_argument('value', nargs='?', help="Provide a string to encrypt.")
    parser.add_argument('-b', '--benchmark', help="Print number of operations per second", required=False, action="store_true")
    parser.add_argument('-p', '--pack', help="Pack a self decoding python file given a file", required=False, action="store_true")
    parser.add_argument('-f', '--file', help="Provide a file to encrypt.", required=False)
    parser.add_argument('-t', '--time', help="Time to decode", required=False, type=int)
    parser.add_argument('-e', '--encrypt', help="Encrypt a file that can be unencrypted in X seconds", required=False, action="store_true")
    parser.add_argument('-d', '--decode', help="Encrypt a file that can be unencrypted in X seconds", required=False)
    parser.add_argument('-u', '--unit', help="Time unit to use when interpreting time input", required=False, default='seconds', choices=[
        'seconds',
        'minutes',
        'hours',
        'days',
        'months',
        'years',
    ])
    parser.add_argument('-U', '--until-date', nargs="+", help="Encode until a date", required=False)
    parser.add_argument('--tz', help="Provide a Time Zone. PST/EST or all of the full codes such as US/Eastern", required=False)
    parser.add_argument('--seconds-until-date', nargs="+", help="Get seconds until a date", required=False)

    # show help if no args
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    Main(args).execute()

if __name__ == "__main__":
    main()