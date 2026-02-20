import * as React from 'react'

export function useOfflineStatus() {
  const [offlineByApi, setOfflineByApi] = React.useState(false)
  const [isOffline, setIsOffline] = React.useState(() =>
    typeof navigator === 'undefined' ? false : !navigator.onLine,
  )

  React.useEffect(() => {
    function onOnline() {
      setIsOffline(false)
      setOfflineByApi(false)
    }
    function onOffline() {
      setIsOffline(true)
    }
    function onApiOffline() {
      setOfflineByApi(true)
    }
    function onApiOnline() {
      setOfflineByApi(false)
    }
    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)
    window.addEventListener('gkp:network-offline', onApiOffline as EventListener)
    window.addEventListener('gkp:network-online', onApiOnline as EventListener)
    return () => {
      window.removeEventListener('online', onOnline)
      window.removeEventListener('offline', onOffline)
      window.removeEventListener('gkp:network-offline', onApiOffline as EventListener)
      window.removeEventListener('gkp:network-online', onApiOnline as EventListener)
    }
  }, [])

  return isOffline || offlineByApi
}
