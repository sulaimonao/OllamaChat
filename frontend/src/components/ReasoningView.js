// frontend/src/components/ReasoningView.js
import React from 'react';
import { Box, Typography, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CodeBlock from './CodeBlock';

const ReasoningView = ({ reasoning }) => {
  if (!reasoning || reasoning.length === 0) {
    return null;
  }

  return (
    <Accordion sx={{ mt: 2 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="body2">Show Reasoning</Typography>
      </AccordionSummary>
      <AccordionDetails>
        {reasoning.map((step, index) => (
          <Box key={index} sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Tool: {step.tool}
            </Typography>
            <Typography variant="body2">Tool Input:</Typography>
            <CodeBlock language="json" value={JSON.stringify(step.tool_input, null, 2)} />
            <Typography variant="body2">Observation:</Typography>
            <CodeBlock language="text" value={step.observation} />
          </Box>
        ))}
      </AccordionDetails>
    </Accordion>
  );
};

export default ReasoningView;
