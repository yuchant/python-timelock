# Time lock a file on your system clock speed

Sequentially encrypted and not able to be parallel processed. Estimates current CPU speed to determine how many layers of encryption to apply to create a relatively predictable time to decode.

Original code and theory is not mine, but I am modifying to fit my needs.

I am just playing around here and the code is pretty terrible.

I mainly needed a way to directly hide a code until a date very easily.

Now I can simply type in `python timelock.py 0981342 -U Friday 7PM` and the system will determine the date I intended, save the output file, etc.

Use:

- pip install pycrypto
- pip install python-dateutil

```bash
# lock until 3:10PM today in PST. Confirm the seconds (ensure positive)
python timelock.py "MY STRING" -U 3:10PM --tz PST

python timelock.py mysecret -U 10PM  # defaults to EST TZ, guided tour.
python timelock.py "String to Encrypt" --until-date 10PM
python timelock.py "String to Encrypt" -U August 20 2015 10PM --tz US/Pacific # some common TZ short codes available.
python timelock.py -f <filename> --pack --time=60 --unit=hours > 60_hours_to_decode.py
python timelock.py --encrypt --file=<filename> --time=60
python timelock.py --decode <filename> # produced above


```
