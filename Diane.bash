!#/bin/bash

# Make Function For recording audio
record()
{
        pw-cat -r "./Log/$time.wav" &

        for ((i = $1; i > 0; --i)); do
                echo $i
                sleep 1
        done

        kill $!
        return
}

# Set Duration And Title with current date and time
time=$(date)
duration=5
# Create file to record to
touch "./Log/$time.wav"
record $duration
exit
