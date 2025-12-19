/**
 * Form Example
 *
 * Shows how to use form components with validation states.
 */

import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Button,
  InputField,
  SearchInput,
  Alert,
  AlertTitle,
  AlertDescription,
} from '../components';

export default function FormExample() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    department: '',
  });
  const [errors, setErrors] = useState({});
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (field) => (e) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.name) newErrors.name = 'Name is required';
    if (!formData.email) newErrors.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Invalid email format';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      setSubmitted(true);
      // Handle form submission
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Success Alert */}
      {submitted && (
        <Alert variant="success" dismissible onDismiss={() => setSubmitted(false)}>
          <AlertTitle>Success!</AlertTitle>
          <AlertDescription>Employee information has been saved.</AlertDescription>
        </Alert>
      )}

      {/* Search Example */}
      <Card>
        <CardHeader>
          <CardTitle>Search Employees</CardTitle>
          <CardDescription>Find employees by name or ID</CardDescription>
        </CardHeader>
        <CardContent>
          <SearchInput
            placeholder="Search employees..."
            aria-label="Search employees"
          />
        </CardContent>
      </Card>

      {/* Form Example */}
      <Card>
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <CardTitle>Add Employee</CardTitle>
            <CardDescription>Enter employee details below</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <InputField
              label="Full Name"
              placeholder="Enter full name"
              value={formData.name}
              onChange={handleChange('name')}
              error={errors.name}
              required
            />

            <InputField
              label="Email Address"
              type="email"
              placeholder="email@example.com"
              value={formData.email}
              onChange={handleChange('email')}
              error={errors.email}
              helperText="We'll use this for notifications"
              required
            />

            <InputField
              label="Department"
              placeholder="Select department"
              value={formData.department}
              onChange={handleChange('department')}
              helperText="Optional field"
            />
          </CardContent>
          <CardFooter className="gap-2">
            <Button type="button" variant="outline">Cancel</Button>
            <Button type="submit">Save Employee</Button>
          </CardFooter>
        </form>
      </Card>

      {/* Validation States */}
      <Card>
        <CardHeader>
          <CardTitle>Input States</CardTitle>
          <CardDescription>Examples of different input states</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <InputField
            label="Default"
            placeholder="Default input"
          />

          <InputField
            label="With Error"
            placeholder="Invalid input"
            error="This field has an error"
          />

          <InputField
            label="With Helper"
            placeholder="Input with helper text"
            helperText="This is a helpful description"
          />

          <InputField
            label="Disabled"
            placeholder="Disabled input"
            disabled
          />
        </CardContent>
      </Card>
    </div>
  );
}
