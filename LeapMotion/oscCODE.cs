// using System.Collections;
// using System.Collections.Generic;
// using UnityEngine;

// public class oscCODE : MonoBehaviour{


//     public OSC osc;.
//     // Start is called before the first frame update
//     void Start()
//     {
        
//     }

//     // Update is called once per frame
//     void Update()
//     {
        
//     }
// }


   
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class oscCODE : MonoBehaviour
{
    public OSC osc; // Référence à la classe OSC pour envoyer des messages
    public Transform leftHandTransform;  // Référence au transform de la main gauche
    public Transform rightHandTransform; // Référence au transform de la main droite

    void Start()
    {
        // Assurez-vous que l'osc est initialisé
        if (osc == null)
        {
            osc = GetComponent<OSC>();
            if (osc == null)
            {
                osc = gameObject.AddComponent<OSC>();
            }
        }
    }

    void Update()
    {
        SendHandPositions();
        // Si vous voulez envoyer les rotations, décommentez la ligne suivante
        // SendHandRotations();
    }

    void SendHandPositions()
    {
        // Envoyer la position de la main gauche
        if (leftHandTransform != null)
        {
            Vector3 leftPos = leftHandTransform.position;
            OscMessage leftMessage = new OscMessage();
            leftMessage.address = "/hand/left/position";
            leftMessage.values.Add(leftPos.x);
            leftMessage.values.Add(leftPos.y);
            leftMessage.values.Add(leftPos.z);
            osc.Send(leftMessage);
        }

        // Envoyer la position de la main droite
        if (rightHandTransform != null)
        {
            Vector3 rightPos = rightHandTransform.position;
            OscMessage rightMessage = new OscMessage();
            rightMessage.address = "/hand/right/position";
            rightMessage.values.Add(rightPos.x);
            rightMessage.values.Add(rightPos.y);
            rightMessage.values.Add(rightPos.z);
            osc.Send(rightMessage);
        }
    }

    void SendHandRotations()
    {
        // Envoyer la rotation de la main gauche
        if (leftHandTransform != null)
        {
            Quaternion leftRot = leftHandTransform.rotation;
            OscMessage leftRotMessage = new OscMessage();
            leftRotMessage.address = "/hand/left/rotation";
            leftRotMessage.values.Add(leftRot.x);
            leftRotMessage.values.Add(leftRot.y);
            leftRotMessage.values.Add(leftRot.z);
            leftRotMessage.values.Add(leftRot.w);
            osc.Send(leftRotMessage);

             Debug.Log("Message OSC envoyé pour la main gauche : " );
        }

        // Envoyer la rotation de la main droite
        if (rightHandTransform != null)
        {
            Quaternion rightRot = rightHandTransform.rotation;
            OscMessage rightRotMessage = new OscMessage();
            rightRotMessage.address = "/hand/right/rotation";
            rightRotMessage.values.Add(rightRot.x);
            rightRotMessage.values.Add(rightRot.y);
            rightRotMessage.values.Add(rightRot.z);
            rightRotMessage.values.Add(rightRot.w);
            osc.Send(rightRotMessage);

             Debug.Log("Message OSC envoyé pour la main droite : " );

        }
    }
}
