import '../tamagui-web.css'

import React, { useEffect, useState } from 'react'
import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native'
import { Stack, useRouter, useSegments } from 'expo-router'
import { useColorScheme, ActivityIndicator, View } from 'react-native'
import { TamaguiProvider } from 'tamagui'
import { PortalProvider } from '@tamagui/portal'

import { tamaguiConfig } from '../tamagui.config'
import { AuthService } from '../services'

export default function RootLayout() {
  const colorScheme = useColorScheme()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const segments = useSegments()

  useEffect(() => {
    checkAuth()
  }, [])

  // Re-check auth when navigating to welcome (to handle logout)
  useEffect(() => {
    if (!isLoading && segments[0] === 'welcome') {
      checkAuth()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [segments])

  useEffect(() => {
    if (isLoading) return

    const inAuthGroup = segments[0] === 'login' || segments[0] === 'welcome'
    const inTabsGroup = segments[0] === '(tabs)'
    const currentTab = segments[1]

    if (!isAuthenticated && !inAuthGroup) {
      // User is not authenticated and not on auth pages, redirect to welcome
      router.replace('/welcome')
    } else if (isAuthenticated) {
      // User is authenticated - redirect to library if on auth pages or index
      if (inAuthGroup) {
        // User is authenticated but on auth pages, redirect to library
        router.replace('/(tabs)/library')
      } else if (inTabsGroup && currentTab === 'index') {
        // User is authenticated but on index page, redirect to library
        router.replace('/(tabs)/library')
      }
    }
  }, [isAuthenticated, segments, isLoading, router])

  const checkAuth = async () => {
    try {
      await AuthService.initialize()
      const authenticated = await AuthService.isAuthenticated()
      setIsAuthenticated(authenticated)
    } catch (error) {
      console.error('Auth check failed:', error)
      setIsAuthenticated(false)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#d9d9d9' }}>
        <ActivityIndicator size="large" color="#5A9FD4" />
      </View>
    )
  }

  return (
    <TamaguiProvider config={tamaguiConfig} defaultTheme={colorScheme!}>
      <PortalProvider shouldAddRootHost>
        <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
          <Stack>
            <Stack.Screen name="welcome" options={{ headerShown: false }} />
            <Stack.Screen name="login" options={{ headerShown: false }} />
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
            <Stack.Screen name="modal" options={{ presentation: 'modal' }} />
          </Stack>
        </ThemeProvider>
      </PortalProvider>
    </TamaguiProvider>
  )
}