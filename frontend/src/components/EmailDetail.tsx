import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export function EmailDetail({ emailId }: { emailId: number | null }) {
  if (!emailId) {
    return <div className="flex items-center justify-center h-full text-muted-foreground">Select an email to view details</div>;
  }

  return (
    <div className="p-6 h-full flex flex-col gap-6 overflow-y-auto">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Email Details (ID: {emailId})</h2>
        <p className="text-muted-foreground">sender@example.com</p>
      </div>
      <Separator />
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p>This is a generated summary of the email content.</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Extracted TODOs</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc pl-5">
            <li>Action item 1</li>
            <li>Action item 2</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
