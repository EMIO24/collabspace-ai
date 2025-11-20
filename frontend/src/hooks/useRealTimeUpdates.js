import { useEffect, useState } from "react";
import { useWebSocket } from "./useWebSocket";

export default function useRealTimeUpdates(eventMap = {}) {
  const ws = useWebSocket();
  const [connectionState, setConnectionState] = useState("connecting");

  useEffect(() => {
    const updateState = () => setConnectionState(ws.connectionState);

    const interval = setInterval(updateState, 500);

    // Register event listeners
    Object.entries(eventMap).forEach(([eventName, callback]) => {
      ws.on(eventName, callback);
    });

    return () => {
      clearInterval(interval);
      Object.entries(eventMap).forEach(([eventName, callback]) => {
        ws.off(eventName, callback);
      });
    };
  }, [ws]);

  return { connectionState };
}
