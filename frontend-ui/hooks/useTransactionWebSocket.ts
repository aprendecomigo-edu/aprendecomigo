import { useState, useEffect, useCallback } from 'react';

export const useTransactionWebSocket = (enabled: boolean) => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transactionUpdates, setTransactionUpdates] = useState<any[]>([]);

  const clearUpdates = useCallback(() => {
    setTransactionUpdates([]);
  }, []);

  useEffect(() => {
    if (!enabled) return;

    // Placeholder WebSocket implementation
    console.log('Transaction WebSocket would connect here');
    setIsConnected(true);

    return () => {
      setIsConnected(false);
    };
  }, [enabled]);

  return {
    isConnected,
    error,
    transactionUpdates,
    clearUpdates,
  };
};
