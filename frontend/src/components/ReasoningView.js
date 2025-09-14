// frontend/src/components/ReasoningView.js
import React from 'react';
import { Box, Typography, Accordion, AccordionSummary, AccordionDetails, ImageList, ImageListItem, ImageListItemBar, List, ListItem, ListItemText } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CodeBlock from './CodeBlock';

const API_URL = 'http://127.0.0.1:8000';

const VideoAnalysisViewer = ({ observation }) => {
    if (!observation) return null;
    return (
        <Box>
            {observation.summary && (
                <>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Summary:</Typography>
                    <Typography variant="body2" sx={{ mb: 1, fontStyle: 'italic' }}>{observation.summary}</Typography>
                </>
            )}
            {observation.transcript && (
                <>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Transcript:</Typography>
                    <Typography component="div" variant="body2" sx={{ mb: 1, maxHeight: 150, overflowY: 'auto', p:1, border: '1px solid #eee', borderRadius: 1 }}>
                        {observation.transcript}
                    </Typography>
                </>
            )}
            {observation.frames && observation.frames.length > 0 && (
                <>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Keyframes:</Typography>
                    <ImageList cols={3} rowHeight={164}>
                        {observation.frames.map((frame, index) => {
                            const imageUrl = `${API_URL}/tools/mm/artifacts/${frame.path}`;
                            return (
                                <ImageListItem key={index}>
                                    <img src={imageUrl} alt={`Keyframe at ${frame.t}s`} loading="lazy" />
                                    <ImageListItemBar
                                        title={`Time: ${frame.t.toFixed(2)}s`}
                                        subtitle={<span>{frame.caption}</span>}
                                    />
                                </ImageListItem>
                            )
                        })}
                    </ImageList>
                </>
            )}
        </Box>
    );
}

const ImageAnalysisViewer = ({ observation }) => {
    if (!observation) return null;
    const imageUrl = `${API_URL}/tools/mm/artifacts/${observation.artifact_path}`;
    return (
        <Box>
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
                <img src={imageUrl} alt="Analyzed content" style={{ maxWidth: '80%', height: 'auto', maxHeight: 300, borderRadius: '4px' }} />
            </Box>
            {observation.captions && observation.captions.length > 0 && (
                 <>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', mt: 1 }}>Captions:</Typography>
                    <List dense>
                        {observation.captions.map((cap, i) => <ListItem key={i}><ListItemText primary={`- ${cap}`} /></ListItem>)}
                    </List>
                </>
            )}
            {observation.ocr && (
                <>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Text Found (OCR):</Typography>
                    <CodeBlock language="text" value={observation.ocr} />
                </>
            )}
        </Box>
    )
}

const AudioAnalysisViewer = ({ observation }) => {
    if (!observation) return null;
    return (
        <Box>
            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Transcript:</Typography>
            <Typography component="div" variant="body2" sx={{ mb: 1, maxHeight: 200, overflowY: 'auto', p:1, border: '1px solid #eee', borderRadius: 1 }}>
                {observation.text}
            </Typography>
        </Box>
    )
}


const ReasoningView = ({ reasoning }) => {
  if (!reasoning || reasoning.length === 0) {
    return null;
  }

  return (
    <Accordion sx={{ mt: 2, bgcolor: '#f9f9f9' }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="body2">Show Reasoning & Sources</Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ p: 1 }}>
        {reasoning.map((step, index) => {
          const isVideo = step.tool === 'multimodal_video_analyzer';
          const isImage = step.tool === 'multimodal_image_analyzer';
          const isAudio = step.tool === 'multimodal_audio_analyzer';
          const isBrowse = step.tool && step.tool.startsWith('browse_');
          const isMultimodal = isVideo || isImage || isAudio;

          let observationContent;
          if (isBrowse && step.observation && Array.isArray(step.observation.sources)) {
            observationContent = (
              <List dense>
                {step.observation.sources.map((s, i) => (
                  <ListItem key={i} component="a" href={s.url} target="_blank">
                    <ListItemText primary={s.title} secondary={s.url} />
                  </ListItem>
                ))}
              </List>
            );
          } else if (typeof step.observation !== 'object' || step.observation === null) {
            observationContent = <CodeBlock language="text" value={String(step.observation)} />;
          } else if (isVideo) {
            observationContent = <VideoAnalysisViewer observation={step.observation} />;
          } else if (isImage) {
            observationContent = <ImageAnalysisViewer observation={step.observation} />;
          } else if (isAudio) {
            observationContent = <AudioAnalysisViewer observation={step.observation} />;
          } else {
            observationContent = <CodeBlock language="json" value={JSON.stringify(step.observation, null, 2)} />;
          }

          return (
            <Box key={index} sx={{ mb: 2, '&:not(:last-child)': { borderBottom: 1, borderColor: 'divider', pb: 2 } }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Tool: {step.tool}
              </Typography>
              {!isMultimodal && (
                  <>
                    <Typography variant="body2">Tool Input:</Typography>
                    <CodeBlock language="json" value={JSON.stringify(step.tool_input, null, 2)} />
                  </>
              )}
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Observation:</Typography>
              {observationContent}
            </Box>
          );
        })}
      </AccordionDetails>
    </Accordion>
  );
};

export default ReasoningView;
