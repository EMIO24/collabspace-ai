import React, { useState, useEffect } from 'react';
import { getTimeEntries, createTimeEntry, deleteTimeEntry } from '../../api/timeTracking';
import styles from './TimeTracking.module.css';

function TimeTracking({ taskId }) {
  const [timeEntries, setTimeEntries] = useState([]);
  const [isTracking, setIsTracking] = useState(false);
  const [startTime, setStartTime] = useState(null);
  const [currentDuration, setCurrentDuration] = useState(0);
  const [manualHours, setManualHours] = useState('');
  const [manualMinutes, setManualMinutes] = useState('');
  const [showManualEntry, setShowManualEntry] = useState(false);

  useEffect(() => {
    loadTimeEntries();
  }, [taskId]);

  useEffect(() => {
    let interval;
    if (isTracking) {
      interval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        setCurrentDuration(elapsed);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTracking, startTime]);

  const loadTimeEntries = async () => {
    try {
      const response = await getTimeEntries(taskId);
      setTimeEntries(response.data);
    } catch (error) {
      console.error('Failed to load time entries:', error);
    }
  };

  const handleStartTracking = () => {
    setIsTracking(true);
    setStartTime(Date.now());
    setCurrentDuration(0);
  };

  const handleStopTracking = async () => {
    if (!startTime) return;

    try {
      const duration = Math.floor((Date.now() - startTime) / 1000);
      const response = await createTimeEntry({
        taskId,
        duration,
        startedAt: new Date(startTime).toISOString(),
      });
      setTimeEntries([response.data, ...timeEntries]);
      setIsTracking(false);
      setStartTime(null);
      setCurrentDuration(0);
    } catch (error) {
      console.error('Failed to save time entry:', error);
    }
  };

  const handleManualEntry = async (e) => {
    e.preventDefault();
    const hours = parseInt(manualHours) || 0;
    const minutes = parseInt(manualMinutes) || 0;
    const duration = (hours * 3600) + (minutes * 60);

    if (duration === 0) return;

    try {
      const response = await createTimeEntry({
        taskId,
        duration,
        startedAt: new Date().toISOString(),
      });
      setTimeEntries([response.data, ...timeEntries]);
      setManualHours('');
      setManualMinutes('');
      setShowManualEntry(false);
    } catch (error) {
      console.error('Failed to add manual entry:', error);
    }
  };

  const handleDelete = async (entryId) => {
    try {
      await deleteTimeEntry(entryId);
      setTimeEntries(timeEntries.filter(e => e.id !== entryId));
    } catch (error) {
      console.error('Failed to delete time entry:', error);
    }
  };

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const totalTime = timeEntries.reduce((sum, entry) => sum + entry.duration, 0);
  const displayTime = isTracking ? currentDuration : 0;

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Time Tracking</h3>

      <div className={styles.totalTime}>
        <span className={styles.totalLabel}>Total Time Logged</span>
        <span className={styles.totalValue}>
          {formatDuration(totalTime + displayTime)}
        </span>
      </div>

      <div className={styles.tracker}>
        {isTracking ? (
          <div className={styles.activeTracker}>
            <div className={styles.timer}>
              <span className={styles.timerIcon}>⏱</span>
              <span className={styles.timerValue}>{formatDuration(currentDuration)}</span>
            </div>
            <button className={styles.stopButton} onClick={handleStopTracking}>
              Stop
            </button>
          </div>
        ) : (
          <div className={styles.trackerButtons}>
            <button className={styles.startButton} onClick={handleStartTracking}>
              <svg viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Start Timer
            </button>
            <button
              className={styles.manualButton}
              onClick={() => setShowManualEntry(!showManualEntry)}
            >
              + Manual Entry
            </button>
          </div>
        )}
      </div>

      {showManualEntry && !isTracking && (
        <form onSubmit={handleManualEntry} className={styles.manualForm}>
          <div className={styles.manualInputs}>
            <div className={styles.timeInput}>
              <input
                type="number"
                className={styles.input}
                value={manualHours}
                onChange={(e) => setManualHours(e.target.value)}
                placeholder="0"
                min="0"
              />
              <span className={styles.inputLabel}>hours</span>
            </div>
            <div className={styles.timeInput}>
              <input
                type="number"
                className={styles.input}
                value={manualMinutes}
                onChange={(e) => setManualMinutes(e.target.value)}
                placeholder="0"
                min="0"
                max="59"
              />
              <span className={styles.inputLabel}>minutes</span>
            </div>
          </div>
          <div className={styles.formActions}>
            <button type="submit" className={styles.saveButton}>
              Add Time
            </button>
            <button
              type="button"
              className={styles.cancelButton}
              onClick={() => {
                setShowManualEntry(false);
                setManualHours('');
                setManualMinutes('');
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {timeEntries.length > 0 && (
        <div className={styles.entriesList}>
          <h4 className={styles.entriesTitle}>Time Entries</h4>
          {timeEntries.map(entry => (
            <div key={entry.id} className={styles.entry}>
              <div className={styles.entryInfo}>
                <span className={styles.entryDuration}>
                  {formatDuration(entry.duration)}
                </span>
                <span className={styles.entryDate}>
                  {new Date(entry.startedAt).toLocaleDateString()}
                </span>
              </div>
              <button
                className={styles.deleteButton}
                onClick={() => handleDelete(entry.id)}
                title="Delete entry"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TimeTracking;