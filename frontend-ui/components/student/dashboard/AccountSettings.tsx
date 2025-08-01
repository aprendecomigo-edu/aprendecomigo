/**
 * Account Settings Component
 * 
 * Provides account and profile management functionality including
 * user information display, notification preferences, and account actions.
 */

import React, { useState } from 'react';
import { 
  Bell,
  CreditCard,
  Download,
  Edit,
  Lock,
  Mail,
  Shield,
  User,
  Trash2,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Settings,
  Eye,
  EyeOff
} from 'lucide-react-native';

import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField, InputIcon, InputSlot } from '@/components/ui/input';
import { 
  Modal, 
  ModalBackdrop, 
  ModalBody, 
  ModalCloseButton, 
  ModalContent, 
  ModalFooter, 
  ModalHeader 
} from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import type { StudentBalanceResponse, UserProfile } from '@/types/purchase';
import { PaymentMethodsSection } from '@/components/student/payment-methods/PaymentMethodsSection';

interface AccountSettingsProps {
  userProfile: UserProfile | null;
  balance: StudentBalanceResponse | null;
  onRefresh: () => Promise<void>;
}

/**
 * User profile information section
 */
function ProfileSection({ 
  userProfile 
}: { 
  userProfile: UserProfile | null 
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: userProfile?.name || '',
    email: userProfile?.email || '',
    phone: userProfile?.phone || '',
  });

  const userInitials = userProfile?.name
    ? userProfile.name
      .split(' ')
      .map((n: string) => n[0])
      .join('')
      .toUpperCase()
    : 'U';

  const handleSave = async () => {
    try {
      // TODO: Implement profile update API call
      // await ProfileApiClient.updateProfile(formData);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update profile:', error);
      // TODO: Show error toast/notification
    }
  };

  const handleCancel = () => {
    setFormData({
      name: userProfile?.name || '',
      email: userProfile?.email || '',
      phone: userProfile?.phone || '',
    });
    setIsEditing(false);
  };

  return (
    <Card className="p-6">
      <VStack space="lg">
        <HStack className="items-center justify-between">
          <Heading size="md" className="text-typography-900">
            Profile Information
          </Heading>
          <Button
            action="secondary"
            variant="outline"
            size="sm"
            onPress={() => setIsEditing(!isEditing)}
          >
            <ButtonIcon as={isEditing ? RefreshCw : Edit} />
            <ButtonText>{isEditing ? 'Cancel' : 'Edit'}</ButtonText>
          </Button>
        </HStack>

        <HStack space="lg" className="items-center">
          <Avatar className="h-20 w-20">
            <AvatarFallbackText className="text-xl">
              {userInitials}
            </AvatarFallbackText>
          </Avatar>
          
          <VStack space="sm" className="flex-1">
            {isEditing ? (
              <VStack space="md">
                <VStack space="xs">
                  <Text className="text-sm font-medium text-typography-800">
                    Full Name
                  </Text>
                  <Input>
                    <InputField
                      value={formData.name}
                      onChangeText={(value) => setFormData(prev => ({ ...prev, name: value }))}
                      placeholder="Enter your full name"
                    />
                  </Input>
                </VStack>
                
                <VStack space="xs">
                  <Text className="text-sm font-medium text-typography-800">
                    Email Address
                  </Text>
                  <Input>
                    <InputField
                      value={formData.email}
                      onChangeText={(value) => setFormData(prev => ({ ...prev, email: value }))}
                      placeholder="Enter your email"
                      keyboardType="email-address"
                    />
                  </Input>
                </VStack>
                
                <VStack space="xs">
                  <Text className="text-sm font-medium text-typography-800">
                    Phone Number
                  </Text>
                  <Input>
                    <InputField
                      value={formData.phone}
                      onChangeText={(value) => setFormData(prev => ({ ...prev, phone: value }))}
                      placeholder="Enter your phone number"
                      keyboardType="phone-pad"
                    />
                  </Input>
                </VStack>

                <HStack space="md">
                  <Button
                    action="primary"
                    variant="solid"
                    size="sm"
                    onPress={handleSave}
                    className="flex-1"
                  >
                    <ButtonText>Save Changes</ButtonText>
                  </Button>
                  <Button
                    action="secondary"
                    variant="outline"
                    size="sm"
                    onPress={handleCancel}
                    className="flex-1"
                  >
                    <ButtonText>Cancel</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            ) : (
              <VStack space="sm">
                <VStack space="xs">
                  <Text className="text-lg font-semibold text-typography-900">
                    {userProfile?.name || 'Unknown User'}
                  </Text>
                  <Text className="text-sm text-typography-600">
                    Student Account
                  </Text>
                </VStack>
                
                <VStack space="xs">
                  <HStack space="xs" className="items-center">
                    <Icon as={Mail} size="sm" className="text-typography-500" />
                    <Text className="text-sm text-typography-700">
                      {userProfile?.email || 'No email provided'}
                    </Text>
                  </HStack>
                  
                  {userProfile?.phone && (
                    <HStack space="xs" className="items-center">
                      <Icon as={User} size="sm" className="text-typography-500" />
                      <Text className="text-sm text-typography-700">
                        {userProfile.phone}
                      </Text>
                    </HStack>
                  )}
                </VStack>
              </VStack>
            )}
          </VStack>
        </HStack>
      </VStack>
    </Card>
  );
}

/**
 * Notification preferences section
 */
function NotificationSettings() {
  const [settings, setSettings] = useState({
    emailNotifications: true,
    sessionReminders: true,
    packageExpiration: true,
    promotionalEmails: false,
    weeklyReports: true,
  });

  const handleToggle = (key: keyof typeof settings) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));
    // TODO: Implement API call to save notification preferences
  };

  return (
    <Card className="p-6">
      <VStack space="lg">
        <HStack className="items-center">
          <Icon as={Bell} size="sm" className="text-typography-600 mr-2" />
          <Heading size="md" className="text-typography-900">
            Notifications
          </Heading>
        </HStack>

        <VStack space="md">
          <HStack className="items-center justify-between">
            <VStack space="xs" className="flex-1">
              <Text className="text-sm font-medium text-typography-800">
                Email Notifications
              </Text>
              <Text className="text-xs text-typography-600">
                Receive important account updates via email
              </Text>
            </VStack>
            <Switch
              size="sm"
              isChecked={settings.emailNotifications}
              onToggle={() => handleToggle('emailNotifications')}
            />
          </HStack>

          <HStack className="items-center justify-between">
            <VStack space="xs" className="flex-1">
              <Text className="text-sm font-medium text-typography-800">
                Session Reminders
              </Text>
              <Text className="text-xs text-typography-600">
                Get reminded about upcoming tutoring sessions
              </Text>
            </VStack>
            <Switch
              size="sm"
              isChecked={settings.sessionReminders}
              onToggle={() => handleToggle('sessionReminders')}
            />
          </HStack>

          <HStack className="items-center justify-between">
            <VStack space="xs" className="flex-1">
              <Text className="text-sm font-medium text-typography-800">
                Package Expiration Alerts
              </Text>
              <Text className="text-xs text-typography-600">
                Get notified when your tutoring hours are about to expire
              </Text>
            </VStack>
            <Switch
              size="sm"
              isChecked={settings.packageExpiration}
              onToggle={() => handleToggle('packageExpiration')}
            />
          </HStack>

          <HStack className="items-center justify-between">
            <VStack space="xs" className="flex-1">
              <Text className="text-sm font-medium text-typography-800">
                Weekly Reports
              </Text>
              <Text className="text-xs text-typography-600">
                Receive weekly summaries of your learning progress
              </Text>
            </VStack>
            <Switch
              size="sm"
              isChecked={settings.weeklyReports}
              onToggle={() => handleToggle('weeklyReports')}
            />
          </HStack>

          <HStack className="items-center justify-between">
            <VStack space="xs" className="flex-1">
              <Text className="text-sm font-medium text-typography-800">
                Promotional Emails
              </Text>
              <Text className="text-xs text-typography-600">
                Receive offers and updates about new features
              </Text>
            </VStack>
            <Switch
              size="sm"
              isChecked={settings.promotionalEmails}
              onToggle={() => handleToggle('promotionalEmails')}
            />
          </HStack>
        </VStack>
      </VStack>
    </Card>
  );
}

/**
 * Security and privacy section
 */
function SecuritySettings() {
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });

  const handlePasswordChange = async () => {
    try {
      // TODO: Implement password change API call
      // await AuthApiClient.changePassword(passwordData);
      setShowPasswordModal(false);
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
    } catch (error) {
      console.error('Failed to change password:', error);
      // TODO: Show error toast/notification
    }
  };

  return (
    <>
      <Card className="p-6">
        <VStack space="lg">
          <HStack className="items-center">
            <Icon as={Shield} size="sm" className="text-typography-600 mr-2" />
            <Heading size="md" className="text-typography-900">
              Security & Privacy
            </Heading>
          </HStack>

          <VStack space="md">
            <Pressable
              className="flex-row items-center justify-between p-3 bg-background-50 rounded-md"
              onPress={() => setShowPasswordModal(true)}
            >
              <HStack space="sm" className="items-center flex-1">
                <Icon as={Lock} size="sm" className="text-typography-600" />
                <VStack space="0">
                  <Text className="text-sm font-medium text-typography-800">
                    Change Password
                  </Text>
                  <Text className="text-xs text-typography-600">
                    Update your account password
                  </Text>
                </VStack>
              </HStack>
              <Icon as={Edit} size="sm" className="text-typography-400" />
            </Pressable>

            <Pressable className="flex-row items-center justify-between p-3 bg-background-50 rounded-md">
              <HStack space="sm" className="items-center flex-1">
                <Icon as={Download} size="sm" className="text-typography-600" />
                <VStack space="0">
                  <Text className="text-sm font-medium text-typography-800">
                    Download My Data
                  </Text>
                  <Text className="text-xs text-typography-600">
                    Export your account information and history
                  </Text>
                </VStack>
              </HStack>
              <Icon as={Download} size="sm" className="text-typography-400" />
            </Pressable>

            <Pressable className="flex-row items-center justify-between p-3 bg-error-50 rounded-md">
              <HStack space="sm" className="items-center flex-1">
                <Icon as={Trash2} size="sm" className="text-error-600" />
                <VStack space="0">
                  <Text className="text-sm font-medium text-error-800">
                    Delete Account
                  </Text>
                  <Text className="text-xs text-error-600">
                    Permanently delete your account and all data
                  </Text>
                </VStack>
              </HStack>
              <Icon as={Trash2} size="sm" className="text-error-400" />
            </Pressable>
          </VStack>
        </VStack>
      </Card>

      {/* Password Change Modal */}
      <Modal isOpen={showPasswordModal} onClose={() => setShowPasswordModal(false)}>
        <ModalBackdrop />
        <ModalContent className="p-6 max-w-md mx-auto">
          <ModalHeader>
            <Heading size="lg">Change Password</Heading>
            <ModalCloseButton />
          </ModalHeader>
          
          <ModalBody>
            <VStack space="md">
              <VStack space="xs">
                <Text className="text-sm font-medium text-typography-800">
                  Current Password
                </Text>
                <Input>
                  <InputField
                    secureTextEntry={!showPasswords.current}
                    value={passwordData.currentPassword}
                    onChangeText={(value) => setPasswordData(prev => ({ ...prev, currentPassword: value }))}
                    placeholder="Enter current password"
                  />
                  <InputSlot className="pr-3" onPress={() => setShowPasswords(prev => ({ ...prev, current: !prev.current }))}>
                    <InputIcon as={showPasswords.current ? EyeOff : Eye} className="text-typography-400" />
                  </InputSlot>
                </Input>
              </VStack>
              
              <VStack space="xs">
                <Text className="text-sm font-medium text-typography-800">
                  New Password
                </Text>
                <Input>
                  <InputField
                    secureTextEntry={!showPasswords.new}
                    value={passwordData.newPassword}
                    onChangeText={(value) => setPasswordData(prev => ({ ...prev, newPassword: value }))}
                    placeholder="Enter new password"
                  />
                  <InputSlot className="pr-3" onPress={() => setShowPasswords(prev => ({ ...prev, new: !prev.new }))}>
                    <InputIcon as={showPasswords.new ? EyeOff : Eye} className="text-typography-400" />
                  </InputSlot>
                </Input>
              </VStack>
              
              <VStack space="xs">
                <Text className="text-sm font-medium text-typography-800">
                  Confirm New Password
                </Text>
                <Input>
                  <InputField
                    secureTextEntry={!showPasswords.confirm}
                    value={passwordData.confirmPassword}
                    onChangeText={(value) => setPasswordData(prev => ({ ...prev, confirmPassword: value }))}
                    placeholder="Confirm new password"
                  />
                  <InputSlot className="pr-3" onPress={() => setShowPasswords(prev => ({ ...prev, confirm: !prev.confirm }))}>
                    <InputIcon as={showPasswords.confirm ? EyeOff : Eye} className="text-typography-400" />
                  </InputSlot>
                </Input>
              </VStack>
            </VStack>
          </ModalBody>
          
          <ModalFooter>
            <HStack space="md" className="w-full">
              <Button
                action="secondary"
                variant="outline"
                size="md"
                onPress={() => setShowPasswordModal(false)}
                className="flex-1"
              >
                <ButtonText>Cancel</ButtonText>
              </Button>
              <Button
                action="primary"
                variant="solid"
                size="md"
                onPress={handlePasswordChange}
                className="flex-1"
              >
                <ButtonText>Update Password</ButtonText>
              </Button>
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}

/**
 * Account summary section
 */
function AccountSummary({ 
  balance, 
  userProfile,
  onRefresh 
}: { 
  balance: StudentBalanceResponse | null;
  userProfile: any;
  onRefresh: () => Promise<void>;
}) {
  if (!balance) {
    return (
      <Card className="p-6">
        <VStack space="md" className="items-center">
          <Icon as={AlertTriangle} size="lg" className="text-warning-500" />
          <Text className="text-typography-600">Unable to load account summary</Text>
          <Button
            action="secondary"
            variant="outline"
            size="sm"
            onPress={onRefresh}
          >
            <ButtonIcon as={RefreshCw} />
            <ButtonText>Retry</ButtonText>
          </Button>
        </VStack>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <VStack space="lg">
        <HStack className="items-center">
          <Icon as={CreditCard} size="sm" className="text-typography-600 mr-2" />
          <Heading size="md" className="text-typography-900">
            Account Summary
          </Heading>
        </HStack>

        <VStack space="md">
          <HStack className="items-center justify-between">
            <Text className="text-sm text-typography-700">
              Account Status:
            </Text>
            <Badge variant="solid" action="success" size="sm">
              <Text className="text-xs">Active</Text>
            </Badge>
          </HStack>

          <HStack className="items-center justify-between">
            <Text className="text-sm text-typography-700">
              Member Since:
            </Text>
            <Text className="text-sm font-medium text-typography-900">
              {/* TODO: Get actual registration date from user profile */}
              January 2024
            </Text>
          </HStack>

          <HStack className="items-center justify-between">
            <Text className="text-sm text-typography-700">
              Total Hours Purchased:
            </Text>
            <Text className="text-sm font-medium text-typography-900">
              {parseFloat(balance.balance_summary.hours_purchased).toFixed(1)}h
            </Text>
          </HStack>

          <HStack className="items-center justify-between">
            <Text className="text-sm text-typography-700">
              Hours Remaining:
            </Text>
            <Text className="text-sm font-medium text-primary-600">
              {parseFloat(balance.balance_summary.remaining_hours).toFixed(1)}h
            </Text>
          </HStack>

          <HStack className="items-center justify-between">
            <Text className="text-sm text-typography-700">
              Active Packages:
            </Text>
            <Text className="text-sm font-medium text-typography-900">
              {balance.package_status.active_packages.length}
            </Text>
          </HStack>
        </VStack>
      </VStack>
    </Card>
  );
}

/**
 * Main Account Settings Component
 */
export function AccountSettings({
  userProfile,
  balance,
  onRefresh,
}: AccountSettingsProps) {
  return (
    <VStack space="lg">
      {/* Header */}
      <VStack space="xs">
        <Heading size="lg" className="text-typography-900">
          Account Settings
        </Heading>
        <Text className="text-sm text-typography-600">
          Manage your profile, preferences, and account security
        </Text>
      </VStack>

      {/* Profile Information */}
      <ProfileSection userProfile={userProfile} />

      {/* Account Summary */}
      <AccountSummary 
        balance={balance} 
        userProfile={userProfile}
        onRefresh={onRefresh}
      />

      {/* Payment Methods */}
      <PaymentMethodsSection />

      {/* Notification Settings */}
      <NotificationSettings />

      {/* Security Settings */}
      <SecuritySettings />
    </VStack>
  );
}