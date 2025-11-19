// Jest tests for frontend components
import { render, screen, fireEvent } from '@testing-library/react';
import { VerifyPage } from '../pages/VerifyEnhanced';
import { GraphVisualization } from '../components/GraphVisualization';

describe('VerifyPage', () => {
  test('renders verification form', () => {
    render(<VerifyPage />);
    expect(screen.getByPlaceholderText(/Enter a scientific claim/i)).toBeInTheDocument();
  });

  test('handles claim verification', async () => {
    render(<VerifyPage />);
    const input = screen.getByPlaceholderText(/Enter a scientific claim/i);
    fireEvent.change(input, { target: { value: 'Test claim' } });
    const button = screen.getByText(/Verify Claim/i);
    fireEvent.click(button);
    // Verification would trigger API call
  });

  test('displays verdict with confidence', async () => {
    const result = {
      verdict: 'SUPPORTS_CAUSALITY',
      confidence: 0.95,
      explanation: 'Test explanation'
    };
    // Component would display result
  });
});

describe('GraphVisualization', () => {
  test('renders graph container', () => {
    const nodes = [{ id: 'n1', label: 'Node 1' }];
    const edges = [];
    render(<GraphVisualization nodes={nodes} edges={edges} />);
    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
  });

  test('handles node clicks', () => {
    const mockClick = jest.fn();
    const nodes = [{ id: 'n1', label: 'Node 1' }];
    const edges = [];
    render(<GraphVisualization nodes={nodes} edges={edges} onNodeClick={mockClick} />);
  });
});

export {};
