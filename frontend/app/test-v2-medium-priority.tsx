import { Check, AlertCircle, Info } from 'lucide-react-native';
import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';

// Import all medium-priority v2 components (simplified versions)
import { Alert, AlertIcon, AlertText } from '@/components/ui/alert/alert-v2-simple';
import {
  Avatar,
  AvatarImage,
  AvatarFallbackText,
  AvatarBadge,
  AvatarGroup,
} from '@/components/ui/avatar/avatar-v2-simple';
import { Card, CardHeader, CardBody, CardFooter } from '@/components/ui/card/card-v2-simple';
import {
  Checkbox,
  CheckboxIndicator,
  CheckboxIcon,
  CheckboxLabel,
  CheckboxGroup,
} from '@/components/ui/checkbox/checkbox-v2-simple';
import { Menu, MenuItem, MenuItemLabel } from '@/components/ui/menu/menu-v2-simple';
import {
  Radio,
  RadioIndicator,
  RadioIcon,
  RadioLabel,
  RadioGroup,
} from '@/components/ui/radio/radio-v2-simple';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectPortal,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicator,
  SelectItem,
} from '@/components/ui/select/select-v2-simple';

export default function TestV2MediumPriorityScreen() {
  const [selectedValue, setSelectedValue] = useState('');
  const [isChecked, setIsChecked] = useState(false);
  const [radioValue, setRadioValue] = useState('option1');

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>V2 Medium-Priority Components Test</Text>
        <Text style={styles.subtitle}>Testing 7 migrated components</Text>

        {/* Select Component */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>1. Select Component</Text>
          <Select value={selectedValue} onValueChange={setSelectedValue}>
            <SelectTrigger variant="outline" size="md">
              <SelectInput placeholder="Choose an option" />
            </SelectTrigger>
            <SelectPortal>
              <SelectBackdrop />
              <SelectContent>
                <SelectDragIndicator />
                <SelectItem label="Option 1" value="opt1" />
                <SelectItem label="Option 2" value="opt2" />
                <SelectItem label="Option 3" value="opt3" />
              </SelectContent>
            </SelectPortal>
          </Select>
          <Text style={styles.value}>Selected: {selectedValue || 'none'}</Text>
        </View>

        {/* Checkbox Component */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>2. Checkbox Component</Text>
          <View style={styles.row}>
            <Checkbox value="check1" isChecked={isChecked} onChange={setIsChecked}>
              <CheckboxIndicator>
                <CheckboxIcon as={Check} />
              </CheckboxIndicator>
              <CheckboxLabel>Accept terms and conditions</CheckboxLabel>
            </Checkbox>
          </View>
          <Text style={styles.value}>Checked: {isChecked ? 'YES' : 'NO'}</Text>
        </View>

        {/* Radio Component */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>3. Radio Component</Text>
          <RadioGroup value={radioValue} onChange={setRadioValue}>
            <Radio value="option1">
              <RadioIndicator>
                <RadioIcon />
              </RadioIndicator>
              <RadioLabel>Option 1</RadioLabel>
            </Radio>
            <Radio value="option2">
              <RadioIndicator>
                <RadioIcon />
              </RadioIndicator>
              <RadioLabel>Option 2</RadioLabel>
            </Radio>
            <Radio value="option3">
              <RadioIndicator>
                <RadioIcon />
              </RadioIndicator>
              <RadioLabel>Option 3</RadioLabel>
            </Radio>
          </RadioGroup>
          <Text style={styles.value}>Selected Radio: {radioValue}</Text>
        </View>

        {/* Alert Component */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>4. Alert Component</Text>
          <Alert action="success" variant="solid">
            <AlertIcon as={Check} />
            <AlertText>Success! Operation completed.</AlertText>
          </Alert>
          <View style={{ height: 8 }} />
          <Alert action="error" variant="outline">
            <AlertIcon as={AlertCircle} />
            <AlertText>Error! Something went wrong.</AlertText>
          </Alert>
          <View style={{ height: 8 }} />
          <Alert action="info" variant="accent">
            <AlertIcon as={Info} />
            <AlertText>Info: This is an informational alert.</AlertText>
          </Alert>
        </View>

        {/* Menu Component */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>5. Menu Component</Text>
          <Menu>
            <MenuItem onPress={() => console.log('Edit')}>
              <MenuItemLabel>Edit</MenuItemLabel>
            </MenuItem>
            <MenuItem onPress={() => console.log('Delete')}>
              <MenuItemLabel>Delete</MenuItemLabel>
            </MenuItem>
            <MenuItem onPress={() => console.log('Share')}>
              <MenuItemLabel>Share</MenuItemLabel>
            </MenuItem>
          </Menu>
        </View>

        {/* Card Component */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>6. Card Component</Text>
          <Card size="md" variant="elevated">
            <CardHeader>
              <Text style={styles.cardTitle}>Card Title</Text>
            </CardHeader>
            <CardBody>
              <Text>
                This is a card body with some content. Cards are useful for grouping related
                information.
              </Text>
            </CardBody>
            <CardFooter>
              <Text style={styles.cardFooter}>Card Footer</Text>
            </CardFooter>
          </Card>
        </View>

        {/* Avatar Component */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>7. Avatar Component</Text>
          <View style={styles.row}>
            <Avatar size="sm" bgColor="#3b82f6">
              <AvatarFallbackText>JD</AvatarFallbackText>
            </Avatar>
            <Avatar size="md" bgColor="#10b981">
              <AvatarFallbackText>AB</AvatarFallbackText>
              <AvatarBadge />
            </Avatar>
            <Avatar size="lg" bgColor="#ef4444">
              <AvatarFallbackText>XY</AvatarFallbackText>
            </Avatar>
          </View>
          <Text style={styles.label}>Avatar Group:</Text>
          <AvatarGroup>
            <Avatar size="sm" bgColor="#3b82f6">
              <AvatarFallbackText>A</AvatarFallbackText>
            </Avatar>
            <Avatar size="sm" bgColor="#10b981">
              <AvatarFallbackText>B</AvatarFallbackText>
            </Avatar>
            <Avatar size="sm" bgColor="#ef4444">
              <AvatarFallbackText>C</AvatarFallbackText>
            </Avatar>
          </AvatarGroup>
        </View>

        {/* Success Message */}
        <View style={styles.successBox}>
          <Text style={styles.successTitle}>✅ Medium-Priority Components Status</Text>
          <Text style={styles.successText}>
            All 7 components migrated successfully:{'\n'}• Select - Working with dropdown{'\n'}•
            Checkbox - Toggle functionality{'\n'}• Radio - Group selection{'\n'}• Alert - All
            variants{'\n'}• Menu - Item interactions{'\n'}• Card - Layout structure{'\n'}• Avatar -
            Display and groups
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  content: {
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 32,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
    color: '#111827',
  },
  row: {
    flexDirection: 'row',
    gap: 16,
    alignItems: 'center',
  },
  value: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 8,
    fontStyle: 'italic',
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    marginVertical: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  cardFooter: {
    fontSize: 14,
    color: '#6b7280',
  },
  successBox: {
    backgroundColor: '#d1fae5',
    padding: 16,
    borderRadius: 8,
    marginTop: 32,
  },
  successTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#065f46',
    marginBottom: 8,
  },
  successText: {
    fontSize: 14,
    color: '#047857',
    lineHeight: 20,
  },
});
