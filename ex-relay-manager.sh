#!/bin/bash

# Configuration
DIR="/opt/exterme-relay-manager"
BIN="$DIR/xray"
CONF_DIR="$DIR/conf.d"
CONF_FILE="$DIR/config.json"
SERVICE_FILE="/etc/systemd/system/exterme-relay-manager.service"
SERVICE_NAME="exterme-relay-manager"

# Colors
GREEN="\e[32m"
BOLD_GREEN="\e[1;32m"
YELLOW="\e[33m"
BLUE="\e[34m"
CYAN="\e[36m"
MAGENTA="\e[35m"
WHITE="\e[37m"
RED="\e[31m"
RESET="\e[0m"

draw_green_line() {
    echo -e "${GREEN}+--------------------------------------------------------+${RESET}"
}

print_art() {
echo -e "\e[1;36m"
echo "======================================================"
echo "        eXtreme Relay Manager                        "
echo "        Dokodemo-Door Tunnel System                 "
echo "======================================================"
echo -e "\e[0m"
}

print_menu() {
    clear
    print_art
    draw_green_line
    echo -e "${GREEN}|${RESET} ${BLUE}1)${RESET} Install Dependencies & Setup Xray            ${GREEN}|${RESET}"
    echo -e "${GREEN}|${RESET} ${YELLOW}2)${RESET} Edit Configurations (Split Files / Single)   ${GREEN}|${RESET}"
    echo -e "${GREEN}|${RESET} ${MAGENTA}3)${RESET} Service Management (Start/Stop/Restart)      ${GREEN}|${RESET}"
    echo -e "${GREEN}|${RESET} ${CYAN}4)${RESET} View Service Logs (Real-time)                ${GREEN}|${RESET}"
    echo -e "${GREEN}|${RESET} ${WHITE}5)${RESET} Check Connection Status (Auto Outbounds)     ${GREEN}|${RESET}"
    echo -e "${GREEN}|${RESET} ${RED}6)${RESET} Run Tunnel Speedtest                         ${GREEN}|${RESET}"
    echo -e "${GREEN}|${RESET} ${BLUE}7)${RESET} Uninstall Project                            ${GREEN}|${RESET}"
    echo -e "${GREEN}|${RESET} ${YELLOW}0)${RESET} Exit                                         ${GREEN}|${RESET}"
    draw_green_line
}

while true; do
    print_menu
    read -p "$(echo -e "${WHITE}Select an option [0-7]: ${RESET}")" choice
    case $choice in
        1)
            mkdir -p "$DIR" "$CONF_DIR"
            apt update && apt install -y unzip curl jq wget speedtest-cli
            wget -O "$DIR/xray.zip" https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip
            unzip -o "$DIR/xray.zip" -d "$DIR"
            chmod +x "$BIN"
            
            # Initializing log file with requested values
            echo '{
  "log": {
    "loglevel": "warning",
    "access": "/opt/exterme-relay-manager/access.log",
    "error": "/opt/exterme-relay-manager/error.log"
  }
}' > "$CONF_DIR/00_log.json"

            # Initializing empty structures for remaining files
            echo '{"inbounds": []}' > "$CONF_DIR/01_inbounds.json"
            echo '{"outbounds": []}' > "$CONF_DIR/02_outbounds.json"
            echo '{"routing": {"rules": []}}' > "$CONF_DIR/03_routing.json"
            echo '{"log": {}, "inbounds": [], "outbounds": [], "routing": {}}' > "$CONF_FILE"

            echo -e "${GREEN}Setup completed and default configs initialized.${RESET}"
            read -p "Press enter to continue..."
            ;;
        2)
            clear
            draw_green_line
            echo -e "${GREEN}|${RESET}            ${BOLD_GREEN}Configuration Editor Menu${RESET}              ${GREEN}|${RESET}"
            draw_green_line
            echo -e "${GREEN}|${RESET} ${BLUE}1)${RESET} 00_log.json                                  ${GREEN}|${RESET}"
            echo -e "${GREEN}|${RESET} ${BLUE}2)${RESET} 01_inbounds.json                              ${GREEN}|${RESET}"
            echo -e "${GREEN}|${RESET} ${BLUE}3)${RESET} 02_outbounds.json                              ${GREEN}|${RESET}"
            echo -e "${GREEN}|${RESET} ${BLUE}4)${RESET} 03_routing.json                                ${GREEN}|${RESET}"
            echo -e "${GREEN}|${RESET} ${YELLOW}5)${RESET} config.json (Single File mode)                 ${GREEN}|${RESET}"
            echo -e "${GREEN}|${RESET} ${RED}0)${RESET} Back to main menu                            ${GREEN}|${RESET}"
            draw_green_line
            read -p "Select a file to edit: " conf_choice
            case $conf_choice in
                1) nano "$CONF_DIR/00_log.json" ;;
                2) nano "$CONF_DIR/01_inbounds.json" ;;
                3) nano "$CONF_DIR/02_outbounds.json" ;;
                4) nano "$CONF_DIR/03_routing.json" ;;
                5) nano "$CONF_FILE" ;;
                *) ;;
            esac
            ;;
        3)
            clear
            draw_green_line
            echo -e "${GREEN}|${RESET}                ${BOLD_GREEN}Service Management${RESET}                  ${GREEN}|${RESET}"
            draw_green_line
            echo -e "${GREEN}|${RESET} ${BLUE}1)${RESET} Start Service                                ${GREEN}|${RESET}"
            echo -e "${GREEN}|${RESET} ${YELLOW}2)${RESET} Stop Service                                 ${GREEN}|${RESET}"
            echo -e "${GREEN}|${RESET} ${MAGENTA}3)${RESET} Restart Service                              ${GREEN}|${RESET}"
            echo -e "${GREEN}|${RESET} ${CYAN}4)${RESET} Create/Reconfigure Systemd Service           ${GREEN}|${RESET}"
            draw_green_line
            read -p "Action: " act
            if [ "$act" == "1" ]; then
                systemctl start $SERVICE_NAME
            elif [ "$act" == "2" ]; then
                systemctl stop $SERVICE_NAME
            elif [ "$act" == "3" ]; then
                systemctl restart $SERVICE_NAME
            elif [ "$act" == "4" ]; then
                echo "Select Xray Execution Mode:"
                echo "1) Directory Mode (-confdir $CONF_DIR)"
                echo "2) Single File Mode (-c $CONF_FILE)"
                read -p "Choice [1-2]: " mode
                
                if [ "$mode" == "1" ]; then
                    EXEC_START="$BIN run -confdir $CONF_DIR"
                else
                    EXEC_START="$BIN -c $CONF_FILE"
                fi

                cat <<EOF > $SERVICE_FILE
[Unit]
Description=Xtreme Relay Manager Service
After=network.target nss-lookup.target

[Service]
User=root
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart=$EXEC_START
Restart=on-failure
RestartPreventExitStatus=23

[Install]
WantedBy=multi-user.target
EOF
                systemctl daemon-reload
                systemctl enable $SERVICE_NAME
                echo -e "${GREEN}Service file created and enabled successfully.${RESET}"
                read -p "Press enter to continue..."
            fi
            ;;
        4)
            journalctl -u $SERVICE_NAME -f
            ;;
        5)
            clear
            echo -e "${CYAN}--- Connection Status (Outbound Ping) ---${RESET}"
            OUTBOUND_IPS=()
            
            if [ -f "$CONF_DIR/02_outbounds.json" ]; then
                OUTBOUND_IPS+=($(jq -r '.outbounds[].settings.vnext[].address // empty' "$CONF_DIR/02_outbounds.json" 2>/dev/null))
                OUTBOUND_IPS+=($(jq -r '.outbounds[].settings.servers[].address // empty' "$CONF_DIR/02_outbounds.json" 2>/dev/null))
            fi
            if [ -f "$CONF_FILE" ]; then
                OUTBOUND_IPS+=($(jq -r '.outbounds[].settings.vnext[].address // empty' "$CONF_FILE" 2>/dev/null))
                OUTBOUND_IPS+=($(jq -r '.outbounds[].settings.servers[].address // empty' "$CONF_FILE" 2>/dev/null))
            fi

            OUTBOUND_IPS=($(echo "${OUTBOUND_IPS[@]}" | tr ' ' '\n' | sort -u))

            if [ ${#OUTBOUND_IPS[@]} -eq 0 ]; then
                echo -e "${RED}No outbound destinations found in config files!${RESET}"
                read -p "Enter custom IP/Domain to ping: " target
            else
                echo "Detected destinations from outbounds:"
                int=1
                for ip in "${OUTBOUND_IPS[@]}"; do
                    echo "$int) $ip"
                    int=$((int+1))
                done
                echo "$int) Enter custom IP/Domain"
                read -p "Select a server to ping [1-$int]: " target_idx

                if [ "$target_idx" -eq "$int" ] 2>/dev/null || [ -z "$target_idx" ]; then
                    read -p "Enter custom IP/Domain: " target
                else
                    target="${OUTBOUND_IPS[$((target_idx-1))]}"
                fi
            fi

            if [ ! -z "$target" ]; then
                echo -e "${GREEN}Pinging $target...${RESET}"
                ping -c 4 "$target"
            else
                echo -e "${RED}Invalid Selection.${RESET}"
            fi
            read -p "Press enter to continue..."
            ;;
        6)
            clear
            echo -e "${MAGENTA}--- Xray Tunnel Speedtest ---${RESET}"
            
            if ! systemctl is-active --quiet $SERVICE_NAME; then
                echo -e "${YELLOW}Warning: $SERVICE_NAME service is not running.${RESET}"
                echo "Starting speedtest via standard network interfaces instead..."
            else
                echo -e "${GREEN}Tunnel service is active. Executing speedtest...${RESET}"
            fi
            
            if command -v speedtest-cli &> /dev/null; then
                speedtest-cli
            else
                echo -e "${RED}speedtest-cli not found. Installing now...${RESET}"
                apt update && apt install -y speedtest-cli
                speedtest-cli
            fi
            read -p "Press enter to continue..."
            ;;
        7)
            systemctl stop $SERVICE_NAME
            systemctl disable $SERVICE_NAME
            rm -rf "$DIR" "$SERVICE_FILE"
            systemctl daemon-reload
            echo -e "${RED}Uninstalled successfully.${RESET}"
            exit
            ;;
        0) exit ;;
    esac
done
