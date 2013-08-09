set term png
set output "downlink.png"
set title "Downlink util"
set xlabel "Time in secs"
set ylabel "Utilization"
plot "/tmp/utils" u 2:7 w lines
