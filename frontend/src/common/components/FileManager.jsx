import React, { useState, useEffect } from 'react';
import {
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
  Grid,
  Typography,
  Checkbox,
  Chip,
  Snackbar,
  TextField,
  CircularProgress,
  Box,
} from '@mui/material';
import {
  CloudUpload,
  CloudDownload,
  Visibility,
  Close,
  Delete,
  ZoomIn,
  ZoomOut,
  RestartAlt,
  AutoAwesome,
  Send,
} from '@mui/icons-material';
import MuiAlert from '@mui/material/Alert';
import axios, { API_BASE_URL, getCsrfToken } from '../api/client.js';
import { useAuth } from '../hooks/AuthContext';

const imageFormats = new Set(['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']);

const buildRagHistory = (messages) => messages
  .filter((message) => ['user', 'assistant'].includes(message.role))
  .filter((message) => String(message.content || '').trim())
  .slice(-10)
  .map((message) => ({
    role: message.role,
    content: String(message.content || '').trim(),
  }));

export default function FileManager({ projectId }) {
  const [files, setFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [openPreview, setOpenPreview] = useState(false);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');
  const [searchQuery, setSearchQuery] = useState('');
  const [fileTypeFilter, setFileTypeFilter] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [imageZoom, setImageZoom] = useState(1);
  const [imagePreviewErrors, setImagePreviewErrors] = useState({});
  const [ragQuestion, setRagQuestion] = useState('');
  const [ragMessages, setRagMessages] = useState([]);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragIndexing, setRagIndexing] = useState(false);
  const { user } = useAuth();
  const isManager = Boolean(user);

  const fetchFiles = () => {
    axios
      .get(`http://localhost:8000/projects/${projectId}/files/`)
      .then((response) => {
        setFiles(response.data?.data?.files || []);
      })
      .catch((error) => {
        console.error('Error fetching file list:', error);
      });
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setOpenSnackbar(true);
  };

  const getErrorMessage = async (error, fallbackMessage) => {
    const data = error.response?.data;

    if (data instanceof Blob) {
      try {
        const text = await data.text();
        try {
          const parsed = JSON.parse(text);
          return parsed.message || parsed.error || fallbackMessage;
        } catch (parseError) {
          return text || fallbackMessage;
        }
      } catch (readError) {
        return fallbackMessage;
      }
    }

    return data?.message || data?.error || error.message || fallbackMessage;
  };

  useEffect(() => {
    fetchFiles();
  }, [projectId]);

  const handleUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    axios
      .post(`http://localhost:8000/projects/${projectId}/files/`, formData, {
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
          setUploadProgress(progress);
        },
      })
      .then((response) => {
        setUploadProgress(0);
        fetchFiles();
        showSnackbar(response.data?.message || '\u6587\u4ef6\u4e0a\u4f20\u6210\u529f');
      })
      .catch(async (error) => {
        console.error('Error uploading file:', error);
        setUploadProgress(0);
        showSnackbar(await getErrorMessage(error, '\u6587\u4ef6\u4e0a\u4f20\u5931\u8d25'), 'error');
      });
  };

  const handleDownload = () => {
    selectedFiles.forEach(async (fileId) => {
      const file = files.find((item) => item.file_id === fileId);
      const fileName = file ? `${file.file_name}${file.file_format}` : String(fileId);

      try {
        const response = await axios.get(`http://localhost:8000/file/download/${fileId}/`, {
          responseType: 'blob',
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', fileName);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Error downloading file:', error);
        showSnackbar(await getErrorMessage(error, '\u6587\u4ef6\u4e0b\u8f7d\u5931\u8d25'), 'error');
      }
    });
  };

  const handleDelete = () => {
    selectedFiles.forEach(async (fileId) => {
      try {
        const response = await axios.delete(`http://localhost:8000/files/${fileId}/`);
        fetchFiles();
        setSelectedFiles([]);
        showSnackbar(response.data?.message || '\u6587\u4ef6\u5220\u9664\u6210\u529f');
      } catch (error) {
        console.error('Error deleting file:', error);
        showSnackbar(await getErrorMessage(error, '\u6587\u4ef6\u5220\u9664\u5931\u8d25'), 'error');
      }
    });
  };


  const handleIndexSelectedFiles = async () => {
    if (selectedFiles.length === 0) {
      showSnackbar('\u8bf7\u5148\u9009\u62e9\u8981\u5165\u5e93\u7684\u6587\u4ef6', 'warning');
      return;
    }

    setRagIndexing(true);
    let successCount = 0;
    let reindexCount = 0;

    for (const fileId of selectedFiles) {
      const selectedFile = files.find((file) => file.file_id === fileId);
      const url = selectedFile?.is_indexed
        ? `http://localhost:8000/files/${fileId}/rag/reindex/`
        : `http://localhost:8000/files/${fileId}/rag/index/`;

      try {
        await axios.post(url);
        successCount += 1;
        if (selectedFile?.is_indexed) {
          reindexCount += 1;
        }
      } catch (error) {
        console.error('Error indexing file:', error);
        showSnackbar(await getErrorMessage(error, '\u6587\u4ef6\u5411\u91cf\u5165\u5e93\u5931\u8d25'), 'error');
      }
    }

    setRagIndexing(false);

    if (successCount > 0) {
      const message = reindexCount > 0
        ? `\u5df2\u5b8c\u6210 ${successCount} \u4e2a\u6587\u4ef6\u5411\u91cf\u5165\u5e93/\u91cd\u65b0\u5165\u5e93`
        : `\u5df2\u5b8c\u6210 ${successCount} \u4e2a\u6587\u4ef6\u5165\u5e93`;
      showSnackbar(message);
      fetchFiles();
    }
  };

  const handleDeleteSelectedFileVectors = async () => {
    const indexedFileIds = selectedFiles.filter((fileId) => {
      const selectedFile = files.find((file) => file.file_id === fileId);
      return selectedFile?.is_indexed;
    });

    if (indexedFileIds.length === 0) {
      showSnackbar('\u8bf7\u5148\u9009\u62e9\u5df2\u5165\u5e93\u7684\u6587\u4ef6', 'warning');
      return;
    }

    setRagIndexing(true);
    let successCount = 0;

    for (const fileId of indexedFileIds) {
      try {
        await axios.delete(`http://localhost:8000/files/${fileId}/rag/vectors/`);
        successCount += 1;
      } catch (error) {
        console.error('Error deleting file vectors:', error);
        showSnackbar(await getErrorMessage(error, '\u6587\u4ef6\u5411\u91cf\u5220\u9664\u5931\u8d25'), 'error');
      }
    }

    setRagIndexing(false);

    if (successCount > 0) {
      showSnackbar(`\u5df2\u5220\u9664 ${successCount} \u4e2a\u6587\u4ef6\u7684\u5411\u91cf`);
      fetchFiles();
    }
  };

  const handleAskRag = async () => {
    const question = ragQuestion.trim();
    if (!question) {
      showSnackbar('\u8bf7\u8f93\u5165\u95ee\u9898', 'warning');
      return;
    }

    const history = buildRagHistory(ragMessages);

    setRagMessages((prev) => [
      ...prev,
      { role: 'user', content: question },
      { role: 'assistant', content: '', sources: [] },
    ]);
    setRagQuestion('');
    setRagLoading(true);

    try {
      const csrfToken = getCsrfToken();
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/rag/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        },
        credentials: 'include',
        body: JSON.stringify({ question, history }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = '\u6587\u6863\u95ee\u7b54\u5931\u8d25';
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.message || errorData.error || errorMessage;
        } catch (parseError) {
          errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      if (!response.body) {
        throw new Error('\u5f53\u524d\u6d4f\u89c8\u5668\u4e0d\u652f\u6301\u6d41\u5f0f\u8f93\u51fa');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.trim()) {
            continue;
          }

          const event = JSON.parse(line);

          if (event.type === 'delta') {
            setRagMessages((prev) => {
              const next = [...prev];
              const lastIndex = next.length - 1;
              next[lastIndex] = {
                ...next[lastIndex],
                content: `${next[lastIndex].content || ''}${event.content || ''}`,
              };
              return next;
            });
          }

          if (event.type === 'done') {
            setRagMessages((prev) => {
              const next = [...prev];
              const lastIndex = next.length - 1;
              next[lastIndex] = {
                ...next[lastIndex],
                sources: event.sources || [],
                content: next[lastIndex].content || '\u6ca1\u6709\u751f\u6210\u56de\u7b54',
              };
              return next;
            });
          }

          if (event.type === 'error') {
            throw new Error(event.message || '\u6587\u6863\u95ee\u7b54\u5931\u8d25');
          }
        }
      }
    } catch (error) {
      console.error('Error asking RAG:', error);
      const errorMessage = await getErrorMessage(error, '\u6587\u6863\u95ee\u7b54\u5931\u8d25');
      showSnackbar(errorMessage, 'error');
      setRagMessages((prev) => {
        const next = [...prev];
        const lastIndex = next.length - 1;
        next[lastIndex] = {
          role: 'assistant',
          content: errorMessage || '\u6587\u6863\u95ee\u7b54\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002',
          error: true,
        };
        return next;
      });
    } finally {
      setRagLoading(false);
    }
  };
  const handleRagKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleAskRag();
    }
  };

  const handlePreview = () => {
    setImageZoom(1);
    setImagePreviewErrors({});
    setOpenPreview(true);
  };

  const handleClosePreview = () => {
    setOpenPreview(false);
    setImageZoom(1);
    setImagePreviewErrors({});
  };

  const handleCheckboxChange = (fileId) => {
    if (selectedFiles.includes(fileId)) {
      setSelectedFiles(selectedFiles.filter((file) => file !== fileId));
    } else {
      setSelectedFiles([...selectedFiles, fileId]);
    }
  };

  const handleCloseSnackbar = () => {
    setOpenSnackbar(false);
  };

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };

  const handleFileTypeFilterChange = (event) => {
    setFileTypeFilter(event.target.value);
  };

  const handleZoomIn = () => {
    setImageZoom((prev) => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setImageZoom((prev) => Math.max(prev - 0.25, 0.5));
  };

  const handleZoomReset = () => {
    setImageZoom(1);
  };

  const selectedFileObjects = selectedFiles
    .map((fileId) => files.find((file) => file.file_id === fileId))
    .filter(Boolean);
  const hasIndexedSelection = selectedFileObjects.some((file) => file.is_indexed);
  const hasOnlyIndexedSelection = selectedFileObjects.length > 0 && selectedFileObjects.every((file) => file.is_indexed);
  const indexActionLabel = hasOnlyIndexedSelection ? '\u91cd\u65b0\u5165\u5e93' : '\u5165\u5e93';

  const fileTypeOptions = Array.from(
    new Set(files.map((file) => file.file_format).filter(Boolean))
  ).sort();

  const filteredFiles = files.filter((file) => {
    const matchesName = file.file_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = !fileTypeFilter || file.file_format === fileTypeFilter;
    return matchesName && matchesType;
  });

  return (
    <div>
      <Grid container spacing={1.5} marginTop={1} wrap="nowrap" alignItems="flex-start" sx={{ width: '100%', maxWidth: '100%', overflow: 'hidden' }}>
        <input
          type="file"
          accept=".pdf,.txt,.jpg,.jpeg,.png,.doc,.docx,.xlsx"
          style={{ display: 'none' }}
          id="file-upload"
          onChange={handleUpload}
        />
        <Grid item xs={7} sx={{ minWidth: 0 }}>
          <Paper elevation={3} sx={{ height: 600, width: '100%', overflow: 'auto' }}>
            <List>
              <ListItem sx={{ gap: 2, alignItems: 'center', flexWrap: 'wrap', position: 'sticky', top: 0, zIndex: 2, bgcolor: 'background.paper', borderBottom: '1px solid #eee' }}>
                <TextField
                  label={'\u641c\u7d22\u6587\u4ef6'}
                  variant="outlined"
                  value={searchQuery}
                  onChange={handleSearchChange}
                  sx={{ width: 330, margin: 1 }}
                />
                <TextField
                  select
                  label={'\u6587\u4ef6\u7c7b\u578b'}
                  variant="outlined"
                  value={fileTypeFilter}
                  onChange={handleFileTypeFilterChange}
                  sx={{ width: 130, margin: 1 }}
                  InputLabelProps={{ shrink: true }}
                  SelectProps={{ native: true }}
                >
                  <option value="">{'\u5168\u90e8'}</option>
                  {fileTypeOptions.map((fileType) => (
                    <option key={fileType} value={fileType}>
                      {fileType}
                    </option>
                  ))}
                </TextField>
                {uploadProgress > 0 && <CircularProgress variant="determinate" value={uploadProgress} />}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, ml: 2, flexShrink: 0 }}>
                  <Grid container spacing={2} alignItems="center" wrap="nowrap">
                    <Grid item>
                      <IconButton aria-label="upload" onClick={() => document.getElementById('file-upload').click()}>
                        <CloudUpload />
                      </IconButton>
                    </Grid>
                    <Grid item>
                      <Typography variant="body2">{'\u4e0a\u4f20'}</Typography>
                    </Grid>
                    <Grid item>
                      <IconButton aria-label="preview" onClick={handlePreview} disabled={selectedFiles.length === 0}>
                        <Visibility />
                      </IconButton>
                    </Grid>
                    <Grid item>
                      <Typography variant="body2">{'\u9884\u89c8'}</Typography>
                    </Grid>
                    <Grid item>
                      <IconButton aria-label="download" onClick={handleDownload} disabled={selectedFiles.length === 0}>
                        <CloudDownload />
                      </IconButton>
                    </Grid>
                    <Grid item>
                      <Typography variant="body2">{'\u4e0b\u8f7d'}</Typography>
                    </Grid>
                    <Grid item>
                      <IconButton
                        aria-label="index-file"
                        onClick={handleIndexSelectedFiles}
                        disabled={selectedFiles.length === 0 || ragIndexing}
                      >
                        {ragIndexing ? <CircularProgress size={22} /> : <AutoAwesome />}
                      </IconButton>
                    </Grid>
                    <Grid item>
                      <Typography variant="body2">{indexActionLabel}</Typography>
                    </Grid>
                    <Grid item>
                      <IconButton
                        aria-label="delete-file-vectors"
                        onClick={handleDeleteSelectedFileVectors}
                        disabled={!hasIndexedSelection || ragIndexing}
                      >
                        <RestartAlt />
                      </IconButton>
                    </Grid>
                    <Grid item>
                      <Typography variant="body2">{'\u5220\u5411\u91cf'}</Typography>
                    </Grid>
                    {isManager && (
                      <Grid item>
                        <IconButton aria-label="delete" onClick={handleDelete} disabled={selectedFiles.length === 0}>
                          <Delete />
                        </IconButton>
                      </Grid>
                    )}
                    {isManager && (
                      <Grid item>
                        <Typography variant="body2">{'\u5220\u9664'}</Typography>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              </ListItem>
              {filteredFiles.map((file) => (
                <ListItem key={file.file_id} divider>
                  <Checkbox
                    checked={selectedFiles.includes(file.file_id)}
                    onChange={() => handleCheckboxChange(file.file_id)}
                  />
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                        <span>{`${file.file_name} ${file.file_format}`}</span>
                        <Chip
                          size="small"
                          label={file.is_indexed ? '\u5df2\u5165\u5e93' : '\u672a\u5165\u5e93'}
                          color={file.is_indexed ? 'success' : 'default'}
                          variant={file.is_indexed ? 'filled' : 'outlined'}
                        />
                      </Box>
                    }
                    secondary={`\u4e0a\u4f20\u4eba\uff1a${file.uploader_name || "\u672a\u77e5"} | \u4e0a\u4f20\u65f6\u95f4\uff1a${file.upload_time || ""}`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
        <Grid item xs={4.6} sx={{ minWidth: 0 }}>
          <Paper
            elevation={3}
            sx={{ height: 600, width: '100%', p: 2, display: 'flex', flexDirection: 'column', boxSizing: 'border-box' }}
          >
            <Typography variant="h6" sx={{ mb: 1 }}>{'\u9879\u76ee\u6587\u6863\u95ee\u7b54'}</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {'\u5148\u9009\u62e9\u6587\u4ef6\u70b9\u51fb\u201c\u5165\u5e93\u201d\uff0c\u518d\u6839\u636e\u9879\u76ee\u6587\u6863\u63d0\u95ee\u3002'}
            </Typography>
            <Box sx={{ flex: 1, overflowY: 'auto', pr: 1, mb: 2, borderTop: '1px solid #eee', borderBottom: '1px solid #eee' }}>
              {ragMessages.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  {'\u6682\u65e0\u5bf9\u8bdd\uff0c\u53ef\u4ee5\u8be2\u95ee\u201c\u8fd9\u4e2a\u9879\u76ee\u6587\u4ef6\u4e3b\u8981\u8bb2\u4e86\u4ec0\u4e48\uff1f\u201d\u6216\u201c\u8d28\u91cf\u68c0\u67e5\u6709\u54ea\u4e9b\u8981\u6c42\uff1f\u201d\u3002'}
                </Typography>
              ) : (
                ragMessages.map((message, index) => (
                  <Box
                    key={`${message.role}-${index}`}
                    sx={{ my: 1.5, display: 'flex', justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start' }}
                  >
                    <Paper
                      variant="outlined"
                      sx={{
                        maxWidth: '88%',
                        p: 1.5,
                        bgcolor: message.role === 'user' ? '#e3f2fd' : '#fafafa',
                        borderColor: message.error ? '#ef9a9a' : '#e0e0e0',
                      }}
                    >
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{message.content}</Typography>
                      {message.sources?.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption" color="text.secondary">{'\u6765\u6e90\uff1a'}</Typography>
                          {message.sources.map((source, sourceIndex) => (
                            <Typography
                              key={`${source.file_id}-${source.chunk_index}-${sourceIndex}`}
                              variant="caption"
                              color="text.secondary"
                              display="block"
                            >
                              {source.file_name}{'\uff08\u7247\u6bb5 '}{source.chunk_index}{'\uff09'}
                            </Typography>
                          ))}
                        </Box>
                      )}
                    </Paper>
                  </Box>
                ))
              )}
              {ragLoading && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, my: 1 }}>
                  <CircularProgress size={18} />
                  <Typography variant="body2" color="text.secondary">{'\u6b63\u5728\u68c0\u7d22\u9879\u76ee\u6587\u6863\u5e76\u751f\u6210\u56de\u7b54...'}</Typography>
                </Box>
              )}
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                value={ragQuestion}
                onChange={(event) => setRagQuestion(event.target.value)}
                onKeyDown={handleRagKeyDown}
                placeholder={'\u8f93\u5165\u4f60\u7684\u95ee\u9898'}
                size="small"
                multiline
                maxRows={3}
                fullWidth
              />
              <Button variant="contained" onClick={handleAskRag} disabled={ragLoading} sx={{ minWidth: 48 }}>
                {ragLoading ? <CircularProgress size={20} color="inherit" /> : <Send />}
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      <Dialog open={openPreview} onClose={handleClosePreview} maxWidth="md" fullWidth>
        <DialogTitle>{'\u6587\u4ef6\u9884\u89c8'}</DialogTitle>
        <DialogContent>
          {selectedFiles.map((fileId) => {
            const file = files.find((item) => item.file_id === fileId);
            const previewUrl = file ? `http://localhost:8000/file/preview/${fileId}` : null;
            const isImage = file && imageFormats.has((file.file_format || '').toLowerCase());
            const imagePreviewError = Boolean(imagePreviewErrors[fileId]);

            if (!file || !previewUrl) {
              console.error(`\u672a\u627e\u5230 ID \u4e3a ${fileId} \u7684\u6587\u4ef6`);
              return null;
            }

            if (isImage) {
              return (
                <Box key={fileId} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">{`${file.file_name}${file.file_format}  ${Math.round(imageZoom * 100)}%`}</Typography>
                    <Box>
                      <IconButton aria-label="zoom-out" onClick={handleZoomOut}>
                        <ZoomOut />
                      </IconButton>
                      <IconButton aria-label="zoom-in" onClick={handleZoomIn}>
                        <ZoomIn />
                      </IconButton>
                      <IconButton aria-label="zoom-reset" onClick={handleZoomReset}>
                        <RestartAlt />
                      </IconButton>
                    </Box>
                  </Box>
                  <Box
                    sx={{
                      width: '100%',
                      height: 500,
                      overflow: 'auto',
                      border: '1px solid #e0e0e0',
                      borderRadius: 1,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: '#fafafa',
                    }}
                  >
                    {imagePreviewError ? (
                      <Typography color="error" variant="body1">
                        只有当前项目成员可以预览文件
                      </Typography>
                    ) : (
                      <img
                        src={previewUrl}
                        alt={file.file_name}
                        onLoad={() => setImagePreviewErrors((prev) => ({ ...prev, [fileId]: false }))}
                        onError={() => setImagePreviewErrors((prev) => ({ ...prev, [fileId]: true }))}
                        style={{
                          transform: `scale(${imageZoom})`,
                          transformOrigin: 'center center',
                          maxWidth: imageZoom <= 1 ? '100%' : 'none',
                          maxHeight: imageZoom <= 1 ? '100%' : 'none',
                          display: 'block',
                        }}
                      />
                    )}
                  </Box>
                </Box>
              );
            }

            return (
              <iframe
                key={fileId}
                title={'\u6587\u4ef6\u9884\u89c8'}
                src={previewUrl}
                style={{ width: '100%', height: '500px', marginBottom: 10, border: 'none' }}
                charSet="UTF-8"
              />
            );
          })}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePreview} startIcon={<Close />}>
            {'\u5173\u95ed'}
          </Button>
        </DialogActions>
      </Dialog>
      <Snackbar
        open={openSnackbar}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <MuiAlert onClose={handleCloseSnackbar} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </MuiAlert>
      </Snackbar>
    </div>
  );
}



