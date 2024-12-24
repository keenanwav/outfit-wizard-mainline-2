import React from 'react';
import { Container, Button, Row, Col } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function HomePage() {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  return (
    <div className="hero-section" style={{ 
      backgroundColor: '#f8f9fa',
      minHeight: '80vh',
      paddingTop: '4rem'
    }}>
      <Container>
        <Row className="align-items-center">
          <Col md={6} className="text-center text-md-start">
            <h1 className="display-4 fw-bold mb-4">Welcome to Our Platform</h1>
            <p className="lead mb-4">
              Join our community and discover amazing features that await you. 
              Sign up now to get started!
            </p>
            {!currentUser && (
              <div className="d-grid gap-2 d-md-flex justify-content-md-start">
                <Button 
                  size="lg" 
                  variant="primary" 
                  onClick={() => navigate('/signup')}
                  className="px-4 me-md-2"
                >
                  Sign Up Now
                </Button>
                <Button 
                  size="lg" 
                  variant="outline-primary" 
                  onClick={() => navigate('/login')}
                  className="px-4"
                >
                  Log In
                </Button>
              </div>
            )}
          </Col>
          <Col md={6} className="text-center">
            <img 
              src="/hero-image.svg" 
              alt="Hero illustration" 
              className="img-fluid"
              style={{ maxWidth: '80%' }}
            />
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default HomePage; 