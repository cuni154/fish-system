#!/data/data/com.termux/files/usr/bin/bash
LOG="/storage/emulated/0/.BBKAppStore/3286/guard.log"
FILE="/storage/emulated/0/鱼系统/constitution.py"
BAK="$HOME/ai_backups_v2"
HASH="ba950c1870e2a9cdae1facc5638cfcbec5eb7ecef0da5436f1b9983dbd304a0c"
echo "$(date) 启动" >> "$LOG"
stop() {
    echo "$(date) 熔断" >> "$LOG"
    pkill -9 -f "learner.py" 2>/dev/null
    pkill -9 -f "inspector.py" 2>/dev/null
    sleep 2
    rm -rf "/storage/emulated/0/鱼系统"/*
    cp -r "$BAK/鱼系统"/* "/storage/emulated/0/鱼系统"/
    echo "$(date) 恢复完成" >> "$LOG"
}
while true; do
    echo "$(date) 心跳" >> "$LOG"
    if [ ! -f "$FILE" ]; then
        echo "$(date) 文件丢失" >> "$LOG"
        stop
    else
        NOW=$(sha256sum "$FILE" | awk '{print $1}')
        if [ "$NOW" != "$HASH" ]; then
            echo "$(date) 哈希变" >> "$LOG"
            stop
        fi
    fi
    sleep 20
done
