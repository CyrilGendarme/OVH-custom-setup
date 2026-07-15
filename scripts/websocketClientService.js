export class WebSocketService {
    constructor({
        port,
        reconnectDelay = 2000,
        onMessage = () => {},
        onOpen = () => {},
        onClose = () => {},
        onError = () => {},
    }) {
            const wsProtocol =
                window.location.protocol === "https:" ? "wss" : "ws";
            const wsIP = "127.0.0.1";

            const wsQueryParam = new URLSearchParams(
                window.location.search,
            ).get("ws");
            const wsOverride =
                typeof window.WS_URL === "string" ? window.WS_URL : "";
            const wsUrl =
                (wsQueryParam && wsQueryParam.trim()) ||
                (wsOverride && wsOverride.trim()) ||
                `${wsProtocol}://${wsIP}:${port}`;

        this.url = wsUrl;
        this.reconnectDelay = reconnectDelay;

        this.onMessage = onMessage;
        this.onOpen = onOpen;
        this.onClose = onClose;
        this.onError = onError;

        this.socket = null;
        this.reconnectTimer = null;
    }

    connect() {
        this.socket = new WebSocket(this.url);

        this.socket.onopen = () => {
            this.onOpen(this.socket);
        };

        this.socket.onmessage = (event) => {
            this.onMessage(event);
        };

        this.socket.onerror = (err) => {
            this.onError(err);
        };

        this.socket.onclose = (event) => {
            this.onClose(event);

            if (!this.reconnectTimer) {
                this.reconnectTimer = setTimeout(() => {
                    this.reconnectTimer = null;
                    this.connect();
                }, this.reconnectDelay);
            }
        };
    }
}