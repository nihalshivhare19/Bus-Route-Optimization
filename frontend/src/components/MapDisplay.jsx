import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function MapDisplay({ mapHtml }) {
  const navigate = useNavigate();

  useEffect(() => {
    if (!mapHtml) {
      navigate('/');
    }
  }, [mapHtml, navigate]);

  return <div>
    <h1>hello</h1>
    <div dangerouslySetInnerHTML={{ __html: mapHtml }} />
  </div>;
}
export default MapDisplay;



