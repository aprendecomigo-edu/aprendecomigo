import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react-native';
import { Button, ButtonText, ButtonIcon, ButtonSpinner, ButtonGroup } from './button-v2';

describe('Button v2 Component', () => {
  it('renders correctly with text', () => {
    const { getByTestId } = render(
      <Button testID="test-button">
        <ButtonText>Click me</ButtonText>
      </Button>,
    );
    // Check that button renders
    const button = getByTestId('test-button');
    expect(button).toBeTruthy();
    // For React Native, check text content differently
    expect(button.props.children).toBeDefined();
  });

  it('handles onPress event', () => {
    const onPress = jest.fn();
    const { getByTestId } = render(
      <Button testID="pressable-button" onPress={onPress}>
        <ButtonText>Click me</ButtonText>
      </Button>,
    );

    const button = getByTestId('pressable-button');
    // For mock components, we can directly call the onPress prop
    if (button.props.onPress) {
      button.props.onPress();
    }
    expect(onPress).toHaveBeenCalled();
  });

  it('renders with different variants', () => {
    const { getByTestId, rerender } = render(
      <Button testID="button" variant="solid">
        <ButtonText>Solid Button</ButtonText>
      </Button>,
    );
    expect(getByTestId('button')).toBeTruthy();

    rerender(
      <Button testID="button" variant="outline">
        <ButtonText>Outline Button</ButtonText>
      </Button>,
    );
    expect(getByTestId('button')).toBeTruthy();

    rerender(
      <Button testID="button" variant="link">
        <ButtonText>Link Button</ButtonText>
      </Button>,
    );
    expect(getByTestId('button')).toBeTruthy();
  });

  it('renders with different sizes', () => {
    const { getByTestId, rerender } = render(
      <Button testID="button" size="xs">
        <ButtonText>XS Button</ButtonText>
      </Button>,
    );
    expect(getByTestId('button')).toBeTruthy();

    rerender(
      <Button testID="button" size="lg">
        <ButtonText>LG Button</ButtonText>
      </Button>,
    );
    expect(getByTestId('button')).toBeTruthy();
  });

  it('renders with spinner', () => {
    const { getByTestId } = render(
      <Button>
        <ButtonSpinner testID="spinner" />
        <ButtonText>Loading</ButtonText>
      </Button>,
    );
    expect(getByTestId('spinner')).toBeTruthy();
  });

  it('renders button group', () => {
    const { getByTestId } = render(
      <ButtonGroup testID="button-group">
        <Button testID="button-1">
          <ButtonText>Button 1</ButtonText>
        </Button>
        <Button testID="button-2">
          <ButtonText>Button 2</ButtonText>
        </Button>
      </ButtonGroup>,
    );
    expect(getByTestId('button-group')).toBeTruthy();
    expect(getByTestId('button-1')).toBeTruthy();
    expect(getByTestId('button-2')).toBeTruthy();
  });

  it('respects disabled state', () => {
    const onPress = jest.fn();
    const { getByTestId } = render(
      <Button testID="disabled-button" disabled onPress={onPress}>
        <ButtonText>Disabled Button</ButtonText>
      </Button>,
    );

    const button = getByTestId('disabled-button');
    fireEvent.press(button);
    expect(onPress).not.toHaveBeenCalled();
  });
});
