# Time lock a file on your system clock speed

Sequentially encrypted and not able to be parallel processed. Estimates current CPU speed to determine how many layers of encryption to apply to create a relatively predictable time to decode.

Original code and theory is not mine, but I am modifying to fit my needs.

I am just playing around here and the code is pretty terrible.

I mainly needed a way to directly hide a code until a date very easily.

Now I can simply type in `python3 timelock.py 0981342 -U Friday 7PM` and the system will determine the date I intended, save the output file, etc.

Use:

- pip install pycryptodome
- pip install python-dateutil


## Short usage example:
```bash
python3 timelock.py "Foobar" --encrypt --time=5 --unit=seconds 
```

It will generate a file such as puzzle_XXXXXXX-X that takes 5 seconds to decode on the current machine.

To decode, run:

```bash
python3 timelock.py --decrypt <filename-generated>
```

## Template to copy/paste

```bash
python3 timelock.py\
    "replace with string to encode"\
    --encrypt\
    --time=5\
    --unit=seconds
python3 timelock.py --decrypt\
    <filename>
```



## More secure method that won't leave history in bash

To avoid leaving the to-lock text in bash history, use a file instead & delete afterwards.

```bash
# edit myfile.txt with contents
python3 timelock.py\
    -f myfile.txt
    --encrypt\
    --time=5\
    --unit=seconds

# delete file so it's gone for good and not recorded in any logs
rm myfile.txt

# start decoding the file
python3 timelock.py --decrypt -f <puzzle_filename>
```







## More examples:


```bash
# lock until 3:10PM today in PST. Confirm the seconds (ensure positive)
python3 timelock.py "MY STRING" -U 3:10PM --tz PST

python3 timelock.py mysecret -U 10PM  # defaults to EST TZ, guided tour.
python3 timelock.py "String to Encrypt" --until-date 10PM
python3 timelock.py "String to Encrypt" -U August 20 2015 10PM --tz US/Pacific # some common TZ short codes available.
python3 timelock.py -f <filename> --pack --time=60 --unit=hours > 60_hours_to_decode.py
python3 timelock.py --encrypt --file=<filename> --time=60
python3 timelock.py --decrypt <filename> # produced above


```



