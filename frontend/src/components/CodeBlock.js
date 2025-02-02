// frontend/src/components/CodeBlock.js
import React, { useState } from 'react';
import { IconButton, Tooltip } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

const CodeBlock = ({ inline, className, children, ...props }) => {
  const [copied, setCopied] = useState(false);
  const codeString = String(children).replace(/\n$/, '');

  if (inline) {
    return <code className={className} {...props}>{children}</code>;
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(codeString)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(err => console.error("Failed to copy!", err));
  };

  return (
    <div style={{ position: 'relative' }}>
      <pre className={className} {...props} style={{ padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '4px', overflowX: 'auto' }}>
        <code>{codeString}</code>
      </pre>
      <Tooltip title={copied ? "Copied!" : "Copy code"} arrow>
        <IconButton 
          onClick={handleCopy} 
          size="small" 
          style={{ position: 'absolute', top: 5, right: 5, backgroundColor: 'rgba(255,255,255,0.8)' }}
        >
          <ContentCopyIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </div>
  );
};

export default CodeBlock;
