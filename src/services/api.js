import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export const authAPI = {
  login: (username, password) =>
    axios.post(`${API_BASE_URL}/auth/login/`, { username, password }),

  register: (username, email, password, password2) =>
    axios.post(`${API_BASE_URL}/auth/register/`, {
      username,
      email,
      password,
      password2,
    }),
};

export const postAPI = {
  getAllPosts: (page = 1, pageSize = 20, ordering = '-created_at') =>
    axios.get(`${API_BASE_URL}/posts/`, {
      params: { page, page_size: pageSize, ordering },
      headers: { Authorization: `Token ${localStorage.getItem('authToken')}` },
    }),

  getPost: (id) => axios.get(`${API_BASE_URL}/posts/${id}/`),

  createPost: (data) =>
    axios.post(`${API_BASE_URL}/posts/`, data, {
      headers: { Authorization: `Token ${localStorage.getItem('authToken')}` },
    }),

  updatePost: (id, data) =>
    axios.put(`${API_BASE_URL}/posts/${id}/`, data, {
      headers: { Authorization: `Token ${localStorage.getItem('authToken')}` },
    }),

  deletePost: (id) =>
    axios.delete(`${API_BASE_URL}/posts/${id}/`, {
      headers: { Authorization: `Token ${localStorage.getItem('authToken')}` },
    }),
};

export const commentAPI = {
  getComments: (postId) =>
    axios.get(`${API_BASE_URL}/comments/`, { params: { post: postId } }),
    headers: { Authorization: `Token ${localStorage.getItem('authToken')}` },

  createComment: (postId, content) =>
    axios.post(`${API_BASE_URL}/comments/`, { post: postId, content }, {
      headers: { Authorization: `Token ${localStorage.getItem('authToken')}` },
    }),
};

export const topicAPI = {
  getAllTopics: () => axios.get(`${API_BASE_URL}/topics/`),
  getTopic: (id) => axios.get(`${API_BASE_URL}/topics/${id}/`),
  createTopic: (data) =>
    axios.post(`${API_BASE_URL}/topics/`, data, {
      headers: { Authorization: `Token ${localStorage.getItem('authToken')}` },
    }),
};

export const reactionAPI = {
  likePost: (postId) =>
    axios.post(
      `${API_BASE_URL}/reactions/`,
      { post: postId, reaction_type: 'like' },
      { headers: { Authorization: `Token ${localStorage.getItem('authToken')}` } }
    ),

  unlikePost: (postId) =>
    axios.delete(`${API_BASE_URL}/reactions/`, {
      params: { post: postId, reaction_type: 'like' },
      headers: { Authorization: `Token ${localStorage.getItem('authToken')}` },
    }),
    
  toggleLike: (postId) => {
    const token = localStorage.getItem('authToken');
    console.log('Token being sent:', token);
    return axios.post(
      `${API_BASE_URL}/posts/${postId}/like/`,
      {},
      { headers: { Authorization: `Token ${token}` } }
    );
  },
};
