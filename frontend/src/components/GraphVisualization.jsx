// Frontend graph visualization component for causal graphs

import React, { useRef, useEffect } from 'react';
import cytoscape from 'cytoscape';

export const GraphVisualization = ({ nodes, edges, onNodeClick }) => {
  const containerRef = useRef(null);
  const cy = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !nodes || !edges) return;

    cy.current = cytoscape({
      container: containerRef.current,
      elements: [
        ...nodes.map(n => ({ data: { id: n.id, label: n.label } })),
        ...edges.map(e => ({ data: { source: e.source, target: e.target, label: e.relation, weight: e.weight } }))
      ],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#3B82F6',
            'label': 'data(label)',
            'width': '50px',
            'height': '50px',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#fff',
            'font-size': '12px'
          }
        },
        {
          selector: 'edge',
          style: {
            'line-color': '#9CA3AF',
            'target-arrow-color': '#9CA3AF',
            'target-arrow-shape': 'triangle',
            'label': 'data(label)',
            'text-background-color': '#fff',
            'text-background-padding': '3px',
            'text-background-opacity': 0.8,
            'curve-style': 'bezier'
          }
        }
      ],
      layout: {
        name: 'cose',
        directed: true,
        animate: true,
        animationDuration: 500,
        nodeSpacing: 50
      }
    });

    cy.current.on('tap', 'node', (evt) => {
      if (onNodeClick) onNodeClick(evt.target.id());
    });

    return () => cy.current?.destroy();
  }, [nodes, edges, onNodeClick]);

  return <div ref={containerRef} className="w-full h-full bg-gray-50 rounded-lg" />;
};

export default GraphVisualization;
