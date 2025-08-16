import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { Button, ButtonText, ButtonIcon, ButtonSpinner, ButtonGroup } from './button-v2';

describe('Button v2 Component', () => {
  it('renders correctly with text', () => {
    const { getByText } = render(
      <Button>
        <ButtonText>Click me</ButtonText>
      </Button>,
    );
    expect(getByText('Click me')).toBeTruthy();
  });

  it('handles onPress event', () => {
    const onPress = jest.fn();
    const { getByText } = render(
      <Button onPress={onPress}>
        <ButtonText>Click me</ButtonText>
      </Button>,
    );

    fireEvent.press(getByText('Click me'));
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
    const { getByText } = render(
      <ButtonGroup>
        <Button>
          <ButtonText>Button 1</ButtonText>
        </Button>
        <Button>
          <ButtonText>Button 2</ButtonText>
        </Button>
      </ButtonGroup>,
    );
    expect(getByText('Button 1')).toBeTruthy();
    expect(getByText('Button 2')).toBeTruthy();
  });

  it('respects disabled state', () => {
    const onPress = jest.fn();
    const { getByText } = render(
      <Button disabled onPress={onPress}>
        <ButtonText>Disabled Button</ButtonText>
      </Button>,
    );

    fireEvent.press(getByText('Disabled Button'));
    expect(onPress).not.toHaveBeenCalled();
  });
});
