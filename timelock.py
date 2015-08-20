#!/usr/bin/env python
DESCRIPTION = """
Theory:
   Time-lock puzzles and timed-release Crypto (1996)
   by Ronald L. Rivest, Adi Shamir, and David A. Wagner

Modified by Yuji Tomita 2015.
"""
import datetime

from Crypto.Util import number, randpool
from Crypto.Cipher import AES
import sys
import time
import argparse

# Init PyCrypto RNG
rnd = randpool.RandomPool()

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
    p = number.getPrime(MOD_BITS/2, rnd.get_bytes)
    q = number.getPrime(MOD_BITS/2, rnd.get_bytes)
    N = p*q
    bignum = number.getRandomNumber(MOD_BITS, rnd.get_bytes)
    start = time.time()
    trials = 100
    for i in range(trials):
        bignum = pow(bignum, 2, N)
    return int(trials/(time.time() - start))

SPEED = calibrate_speed()
SAVE_INTERVAL = SPEED * 10 * MINUTE

def aes_pad(msg):
    return msg + (16 - len(msg) % 16) * '\0'

def aes_encode(msg, key):
    return AES.new(number.long_to_bytes(key)).encrypt(aes_pad(msg))

def aes_decode(ciphertext, key):
    return AES.new(number.long_to_bytes(key)).decrypt(ciphertext)

# Routine adapted from Anti-Emulation-through-TimeLock-puzzles
def makepuzzle(t):

    # Generate 512-bit primes
    p = number.getPrime(MOD_BITS/2, rnd.get_bytes)
    q = number.getPrime(MOD_BITS/2, rnd.get_bytes)
    N = p*q
    totient = (p-1)*(q-1)

    key = number.getRandomNumber(AES_BITS, rnd.get_bytes)
    a = number.getRandomNumber(MOD_BITS, rnd.get_bytes) % N

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
    filename = 'puzzle_%d-%d' % (p['cipher_key'] % 1000000000000, p['steps']/SAVE_INTERVAL)
    with open(filename, 'w') as f:
        f.write('# Run ./timelock FILENAME > OUTFILE to decode\n')
        putestimation(f, p)
        f.write('\n')
        f.write(state)
    print >>sys.stderr, "saved state:", filename

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
    print >>sys.stderr
    return (p['cipher_key'] - tmp) % N

def _unpack():
    solution = solve_puzzle(puzzle)
    print >>sys.stderr, "solution =", solution
    if 'ciphertext' in puzzle:
        result = aes_decode(puzzle['ciphertext'], solution)
        print result
    with open('decoded.txt', 'a') as f:
        f.write(result + "\n")


def _usage():
    if puzzle:
        print """*** This is a self-decoding file ***

If no parameter is given, the embedded puzzle will be decoded.
"""
    print """Usage: ./timelock.py <PARAM>
    --h|help                    display this message
    --new [time]                create a sample puzzle with solution time 'time'
    --encrypt <file> [time]     encode a file using AES with a random key
    --pack <file> [time]        pack a self-decoding file using this script
    --benchmark                 print number of operations per second
    <saved state>               print puzzle solution to stdout
    """
    exit(2)

def _new_key_time0(time):
    try:
        time = int(sys.argv[2]) * SECOND
    except:
        time = 30 * SECOND
    print "Creating test puzzle with difficulty time %d" % time
    (key, puzzle) = makepuzzle(time*SPEED)
    print "key:", str(key) # Recover the key
    save_puzzle(puzzle)

def _encrypt_file_time0(file, time, value=None):
    if value is not None:
        msg = value
    else:
        msg = open(file).read()
    try:
        time = int(sys.argv[3]) * SECOND
    except:
        time = 30 * SECOND
    (key, puzzle) = makepuzzle(time*SPEED)
    puzzle['ciphertext'] = aes_encode(msg, key)
    save_puzzle(puzzle)

def _pack_file_time0(self, file, time, value=None, save_to_file=None):
    if save_to_file is not None:
        import StringIO
        stdout = sys.stdout
        sys.stdout = StringIO.StringIO()
    if value is not None:
        msg = value
    else:
        msg = open(file).read()

    try:
        time = int(time)
    except:
        try:
            time = int(sys.argv[3]) * SECOND
        except:
            time = 30 * SECOND
    (key, puzzle) = makepuzzle(time*SPEED)
    puzzle['ciphertext'] = aes_encode(msg, key)
    print "#!/usr/bin/env python"
    for line in DESCRIPTION.split('\n'):
        print "#", line
    print "# Run this program to recover the original message."
    print "# (scroll down see the program that generated this file)"
    print "#"
    putestimation(sys.stdout, puzzle)
    print "#"
    print
    print "puzzle =", puzzle
    print open(self).read()
    if save_to_file is not None:
        with open(save_to_file, 'w') as f:
            f.write(sys.stdout.getvalue())
            sys.stdout = stdout

def _decode_file(file):
    try:
        puzzle = eval(open(file).read())
    except Exception, e:
        print "Error parsing saved state.", e
        exit(1)
    solution = solve_puzzle(puzzle)
    print >>sys.stderr, "solution =", solution
    if 'ciphertext' in puzzle:
        print aes_decode(puzzle['ciphertext'], solution)



# class ArgList(list):
#     def __init__(self, *args):
#         list.__init__(self, *args)
#         self.base = self[0]
#         self.first = self[1]
#         self.second = self[2]
#         self.third = self[3]

#     def __getitem__(self, i):
#         if i >= len(self):
#             return None
#         return list.__getitem__(self, i)



# def main():
#     args = ArgList(sys.argv)
#     if args.first == '-h' or args.first == '--help':
#         _usage()
#     elif len(args) == 1 and puzzle:
#         _unpack()
#     elif len(args) == 1:
#         _usage()
#     elif args.first == '--new':
#         _new_key_time0(args.second)
#     elif args.first == '--benchmark':
#         print "%d %d-bit modular exponentiations per second" % (SPEED, MOD_BITS)
#     elif args.first == '--encrypt':
#         _encrypt_file_time0(args.second, args.third)
#     elif args[1] == '--pack':
#         _pack_file_time0(args.base, args.second, args.third)
#     else:
#         _decode_file(args.first)

    # print """Usage: ./timelock.py <PARAM>
    # --h|help                    display this message
    # --new [time]                create a sample puzzle with solution time 'time'
    # --encrypt <file> [time]     encode a file using AES with a random key
    # --pack <file> [time]        pack a self-decoding file using this script
    # --benchmark                 print number of operations per second
    # <saved state>               print puzzle solution to stdout

class Main(object):
    def __init__(self, args):
        self.args = args
        print >> sys.stderr, args

    def execute(self):
        if self.args.benchmark:
            self.benchmark()
        elif self.args.pack:
            self.pack()
        elif self.args.seconds_until_date or self.args.until_date:
            self.seconds_until_date(self.args.seconds_until_date or self.args.until_date)
        elif self.args.encrypt:
            self.encrypt()
        else:
            sys.exit(1)

    def exit(self, msg=''):
        print >> sys.stderr, u"Exit: %s" % msg
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
        print >> sys.stderr, "Packing... ", seconds, save_to_file
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
        print >> sys.stderr, "Calculated seconds to: %s" % seconds
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
        print >> sys.stderr,'Calculating time until a date %s' % arg
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
        print >> sys.stderr, "Server Now UTC: ",  server_utc
        server_est = server_utc.astimezone(pytz.timezone('US/Eastern'))
        print >> sys.stderr,  "Server Now EST: ", server_est

        if len(arg) > 1:
            arg = u' '.join(arg)
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
            proceed = raw_input("No TZ passed. Assuming EST.\nProceed?\ny/n: ")
            if proceed != 'y':
                self.exit("Exited")
            tz = pytz.timezone('US/Eastern')
            target_date_tz = tz.localize(target_date)
            target_date_utc = target_date_tz.astimezone(pytz.utc)
        target_date_string = target_date_tz.strftime('%A, %B %Y at %I%p %Z').strip()
        print >> sys.stderr, "Target Date UTC: ", target_date_utc
        print >> sys.stderr, "Target Date %s: " % tz, target_date_string

        delta = target_date_tz - server_utc
        seconds = delta.total_seconds()


        default_filename = '__'.join((
            'target_',
            target_date_string.replace(' ', '_').replace(',', ''),
            '.py'
        ))
        proceed = raw_input("""Time difference is {delta}.
Seconds: {seconds:.0f}
Minutes: {minutes:.0f}
Hours: {hours:.1f}
Days: {days:.2f}
Target Unlock Date: {target_date}
----
Encrypt?
y/n: """.format(
                delta=delta,
                seconds=seconds,
                minutes=seconds/MINUTE,
                hours=seconds/HOUR,
                days=seconds/DAY,
                target_date=target_date_string
            ))
        if proceed == 'y':
            filename = raw_input("Enter the output file name or leave blank to use %s as the file name:\n" % default_filename)
            self.pack(seconds, save_to_file=filename or default_filename)
        else:
            self.exit("Exited due to user input")
        return seconds

    def get_value_to_encode(self):
        if self.args.file:
            with open(self.args.file) as f:
                return f.read()
        elif self.args.value:
            return self.args.value
        self.exit("No string or file provided to encode")

    def benchmark(self):
        print "%d %d-bit modular exponentiations per second" % (SPEED, MOD_BITS)


def main():
    if puzzle:
        print >> sys.stderr, 'this is a self decoding file - decoding.'
        _unpack()
        return

    parser = argparse.ArgumentParser()
    parser.add_argument('value', nargs='?', help="Provide a string to encrypt.")
    parser.add_argument('-b', '--benchmark', help="Print number of operations per second", required=False, action="store_true")
    parser.add_argument('-p', '--pack', help="Pack a self decoding python file given a file", required=False, action="store_true")
    parser.add_argument('-f', '--file', nargs=1, help="Provide a file to encrypt.", required=False)
    parser.add_argument('-t', '--time', help="Time to decode", required=False, type=int)
    parser.add_argument('-e', '--encrypt', help="Encrypt a file that can be unencrypted in X seconds", required=False, action="store_true")
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