import React, { useState } from "react";
import {
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ImageBackground,
} from "react-native";
import {
  Button,
  H2,
  H4,
  Input,
  YStack,
  XStack,
  Text,
  ScrollView,
} from "tamagui";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { AuthService } from "../services";

const loginBackground = require("../assets/images/Login/login_background.png");

export default function LoginScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert("錯誤", "請輸入使用者名稱和密碼");
      return;
    }

    setLoading(true);
    try {
      await AuthService.login(username.trim(), password);
      // Navigate to library after successful login
      router.replace("/(tabs)/library");
    } catch (error) {
      console.error("Login error:", error);
      Alert.alert(
        "登入失敗",
        error instanceof Error ? error.message : "請檢查您的使用者名稱和密碼"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert("錯誤", "請輸入使用者名稱和密碼");
      return;
    }

    if (password.length < 8) {
      Alert.alert("錯誤", "密碼必須至少 8 個字元");
      return;
    }

    setLoading(true);
    try {
      await AuthService.register(
        username.trim(),
        password,
        email.trim() || undefined
      );
      // Navigate to library after successful registration
      router.replace("/(tabs)/library");
    } catch (error) {
      console.error("Registration error:", error);
      Alert.alert(
        "註冊失敗",
        error instanceof Error ? error.message : "註冊時發生錯誤"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <ImageBackground
      source={loginBackground}
      style={{ flex: 1 }}
      resizeMode="cover"
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
      >
        <ScrollView flex={1}>
          <YStack
            flex={1}
            px={24}
            pt={insets.top + 40}
            pb={insets.bottom + 20}
            gap={24}
          >
          <YStack gap={12} alignItems="center">
            <H2 color="#404040" fontWeight={"bold"}>
              {isLogin ? "登入" : "註冊"}
            </H2>
            <H4 color="#666" textAlign="center">
              {isLogin ? "請登入以存取您的故事庫" : "建立新帳號開始創作故事"}
            </H4>
          </YStack>

          <YStack gap={16} bg="white" p={24} borderRadius={12}>
            <YStack gap={8}>
              <Text color="#404040" fontWeight="600">
                使用者名稱
              </Text>
              <Input
                size="$4"
                value={username}
                onChangeText={setUsername}
                placeholder="輸入使用者名稱"
                autoCapitalize="none"
                autoCorrect={false}
                editable={!loading}
              />
            </YStack>

            {!isLogin && (
              <YStack gap={8}>
                <Text color="#404040" fontWeight="600">
                  Email（選填）
                </Text>
                <Input
                  size="$4"
                  value={email}
                  onChangeText={setEmail}
                  placeholder="輸入 email"
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  editable={!loading}
                />
              </YStack>
            )}

            <YStack gap={8}>
              <Text color="#404040" fontWeight="600">
                密碼
              </Text>
              <Input
                size="$4"
                value={password}
                onChangeText={setPassword}
                placeholder={isLogin ? "輸入密碼" : "至少 8 個字元"}
                secureTextEntry
                autoCapitalize="none"
                autoCorrect={false}
                editable={!loading}
              />
            </YStack>

            <YStack gap={12} mt={12}>
              {loading ? (
                <YStack py={12} alignItems="center">
                  <ActivityIndicator size="large" color="#5A9FD4" />
                </YStack>
              ) : (
                <>
                  <Button
                    size="$4"
                    bg="#5A9FD4"
                    color="white"
                    onPress={isLogin ? handleLogin : handleRegister}
                    pressStyle={{ opacity: 0.8 }}
                  >
                    {isLogin ? "登入" : "註冊"}
                  </Button>

                  <XStack gap={4} justifyContent="center" alignItems="center">
                    <Text color="#666" fontSize={14}>
                      {isLogin ? "還沒有帳號？" : "已經有帳號？"}
                    </Text>
                    <Button
                      size="$3"
                      chromeless
                      onPress={() => {
                        setIsLogin(!isLogin);
                        setPassword("");
                        setEmail("");
                      }}
                      color="#5A9FD4"
                      pressStyle={{ opacity: 0.7 }}
                    >
                      {isLogin ? "註冊" : "登入"}
                    </Button>
                  </XStack>
                </>
              )}
            </YStack>
          </YStack>

          <YStack alignItems="center" mt={20}>
            <Button
              chromeless
              size="$3"
              color="white"
              onPress={() => router.back()}
              disabled={loading}
            >
              返回
            </Button>
          </YStack>
        </YStack>
      </ScrollView>
    </KeyboardAvoidingView>
    </ImageBackground>
  );
}
