import { render, screen } from '@testing-library/react';

import ParrotLogoIcon from './ParrotLogoIcon';

describe('ParrotLogoIcon', () => {
  test('renders the institutional logo svg with default color and size', () => {
    const { container } = render(<ParrotLogoIcon />);

    const svg = container.querySelector('svg');
    const firstPath = container.querySelector('path');

    expect(svg).toHaveAttribute('viewBox', '0 0 375 375');
    expect(svg).toHaveAttribute('width', '48');
    expect(svg).toHaveAttribute('height', '48');
    expect(svg).toHaveAttribute('aria-hidden', 'true');
    expect(firstPath).toHaveAttribute('fill', '#067f38');
  });

  test('supports custom size, color, className, and speech bubble', () => {
    const { container } = render(
      <ParrotLogoIcon size={38} color="#ffffff" className="brand-mark" showSpeech speechText="You should be here!" />
    );

    const wrapper = container.firstElementChild;
    const svg = container.querySelector('svg');
    const firstPath = container.querySelector('path');

    expect(wrapper).toHaveClass('brand-mark');
    expect(svg).toHaveAttribute('width', '38');
    expect(svg).toHaveAttribute('height', '38');
    expect(firstPath).toHaveAttribute('fill', '#ffffff');
    expect(screen.getByText('You should be here!')).toBeInTheDocument();
  });
});

