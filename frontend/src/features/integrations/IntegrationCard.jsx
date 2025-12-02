import React from 'react';
import { Github, Slack, Figma, Trello, CheckCircle, Plus } from 'lucide-react';
import Button from '../../components/ui/Button/Button';
import styles from './Integrations.module.css';

const ICONS = {
  github: <Github size={24} />,
  slack: <Slack size={24} />,
  figma: <Figma size={24} />,
  trello: <Trello size={24} />
};

const IntegrationCard = ({ integration, onConnect }) => {
  const isConnected = integration.status === 'connected';

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div className={styles.iconWrapper}>
          {ICONS[integration.provider] || <Plus size={24} />}
        </div>
        <span className={`${styles.statusBadge} ${isConnected ? styles.connected : styles.disconnected}`}>
          {isConnected ? 'Active' : 'Not Connected'}
        </span>
      </div>

      <h3 className={styles.name}>{integration.name}</h3>
      <p className={styles.description}>{integration.description}</p>

      <div className={styles.footer}>
        {isConnected ? (
          <Button variant="ghost" disabled className="w-full">
            <CheckCircle size={16} className="mr-2" /> Connected
          </Button>
        ) : (
          <Button 
            className="w-full" 
            onClick={() => onConnect(integration)}
          >
            Connect
          </Button>
        )}
      </div>
    </div>
  );
};

export default IntegrationCard;