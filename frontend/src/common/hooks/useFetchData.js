import { useState, useEffect } from 'react';
import axios from '../api/client.js';

const useFetchData = (url) => {
  const [data, setData] = useState([]);
  const [error, setError] = useState(null);

  const fetchData = async () => {
      try {
        const response = await axios.get(url);
        setData(response.data);
      } catch (error) {
        setError("Error fetching data: " + error.message);
      }
    };
  useEffect(() => {
    fetchData();
  }, [url]);

  return { data, error, fetchData};
};

export default useFetchData;

