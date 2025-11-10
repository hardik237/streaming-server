# get the system ip address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

sudo docker compose up -d

echo ""
echo "=============================================="
echo "Server is running at http://$IP_ADDRESS:8501"
echo "=============================================="