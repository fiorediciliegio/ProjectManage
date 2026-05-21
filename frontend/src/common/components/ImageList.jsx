import React, { useState, useEffect } from 'react';
import axios from '../api/client.js';
import ImageList from '@mui/material/ImageList';
import ImageListItem from '@mui/material/ImageListItem';
import ImageListItemBar from '@mui/material/ImageListItemBar';
import ListSubheader from '@mui/material/ListSubheader';
import IconButton from '@mui/material/IconButton';
import InfoIcon from '@mui/icons-material/Info';

axios.interceptors.request.use(request => {
  console.log('Starting Request', request);
  return request;
});

axios.interceptors.response.use(response => {
  console.log('Response:', response);
  return response;
}, error => {
  console.error('Error Response:', error);
  return Promise.reject(error);
});

export default function TitlebarImageList({ projectId }) {
  const [itemData, setItemData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchImageMetadata = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/safety/report/image/${projectId}/metadata/`);
        const metadata = response.data.images;

        const imagePromises = metadata.map(async (item) => {
          try {
            const imgResponse = await axios.get(`http://localhost:8000${item.img_url}`, {
              responseType: 'blob'
            });
            const imgUrl = URL.createObjectURL(imgResponse.data);
            return { ...item, img: imgUrl };
          } catch (error) {
            console.error(`Error fetching image ${item.img_url}:`, error);
            return { ...item, img: null };
          }
        });

        const updatedData = await Promise.all(imagePromises);
        setItemData(updatedData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching the images:', error);
        setLoading(false);
      }
    };

    fetchImageMetadata();

    // Clean up URL object references when the component unmounts
    return () => {
      itemData.forEach(item => {
        if (item.img) {
          URL.revokeObjectURL(item.img);
        }
      });
    };
  }, [projectId]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <ImageList sx={{ width: 500, height: 450 }}>
      <ImageListItem key="Subheader" cols={2}>
        <ListSubheader component="div">December</ListSubheader>
      </ImageListItem>
      {itemData.map((item, index) => (
        <ImageListItem key={index}>
          {item.img ? (
            <img
              src={item.img}
              alt={item.title || 'Image'}
              loading="lazy"
              onError={(e) => { e.target.onerror = null; e.target.src = "fallback_image_url"; }} 
            />
          ) : (
            <div style={{ width: 248, height: 248, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0f0f0' }}>
              <span>Image Not Available</span>
            </div>
          )}
          <ImageListItemBar
            title={item.title || 'No Title'}
            subtitle={item.author || 'Unknown Author'}
            actionIcon={
              <IconButton
                sx={{ color: 'rgba(255, 255, 255, 0.54)' }}
                aria-label={`info about ${item.title || 'No Title'}`}
              >
                <InfoIcon />
              </IconButton>
            }
          />
        </ImageListItem>
      ))}
    </ImageList>
  );
}

