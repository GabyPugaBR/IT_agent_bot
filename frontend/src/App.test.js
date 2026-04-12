import { render, screen } from '@testing-library/react';
import App from './App';

test('renders constellations support heading', () => {
  render(<App />);
  const supportLaunchers = screen.getAllByText(/it agent/i);
  expect(supportLaunchers.length).toBeGreaterThan(0);
});
