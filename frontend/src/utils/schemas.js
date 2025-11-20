import PropTypes from 'prop-types';

export const UserShape = PropTypes.shape({
  id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  email: PropTypes.string,
  first_name: PropTypes.string,
  last_name: PropTypes.string,
  avatar: PropTypes.string,
});

export const WorkspaceShape = PropTypes.shape({
  id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  name: PropTypes.string,
  slug: PropTypes.string,
  description: PropTypes.string,
  is_public: PropTypes.bool,
  owner: UserShape,
  created_at: PropTypes.string,
});

export const ProjectShape = PropTypes.shape({
  id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  workspace: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  name: PropTypes.string,
  description: PropTypes.string,
  status: PropTypes.string,
  created_at: PropTypes.string,
});

export const TaskShape = PropTypes.shape({
  id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  title: PropTypes.string,
  description: PropTypes.string,
  status: PropTypes.string,
  assignee: UserShape,
  due_date: PropTypes.string,
});
